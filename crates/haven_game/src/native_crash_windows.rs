//! Windows-native crash capture for failures that bypass Rust panic unwinding.
//!
//! This module intentionally uses only Win32/DbgHelp entry points in the exception
//! filter so stack-overflow handling does not depend on Rust allocation or panic
//! machinery. The runtime reserves an emergency stack guarantee before installing
//! the filter.

#![cfg(target_os = "windows")]

use std::ffi::c_void;
use std::sync::atomic::{AtomicI32, AtomicU32, Ordering};
use std::sync::OnceLock;

const GENERIC_WRITE: u32 = 0x4000_0000;
const CREATE_ALWAYS: u32 = 2;
const FILE_ATTRIBUTE_NORMAL: u32 = 0x0000_0080;
const MINI_DUMP_WITH_HANDLE_DATA: u32 = 0x0000_0004;
const MINI_DUMP_WITH_UNLOADED_MODULES: u32 = 0x0000_0020;
const MINI_DUMP_WITH_THREAD_INFO: u32 = 0x0000_1000;
const EXCEPTION_EXECUTE_HANDLER: i32 = 1;
const EXCEPTION_ACCESS_VIOLATION: u32 = 0xC000_0005;
const EXCEPTION_STACK_OVERFLOW: u32 = 0xC000_00FD;

pub(crate) const PHASE_BOOT: u32 = 0;
pub(crate) const PHASE_LIVE_BRIDGE: u32 = 1;
pub(crate) const PHASE_UPDATE: u32 = 2;
pub(crate) const PHASE_APPEARANCE_RELOAD: u32 = 3;
pub(crate) const PHASE_DRAW: u32 = 4;
pub(crate) const PHASE_PAUSE_DRAW: u32 = 5;
pub(crate) const PHASE_PRESENT: u32 = 6;
pub(crate) const PHASE_TELEMETRY: u32 = 7;
pub(crate) const PHASE_SNAPSHOT: u32 = 8;
pub(crate) const PHASE_RUNTIME_EXIT: u32 = 9;
pub(crate) const PHASE_DRAW_CLEAR: u32 = 10;
pub(crate) const PHASE_DRAW_MAP: u32 = 11;
pub(crate) const PHASE_DRAW_STRUCTURAL_CLIFFS: u32 = 12;
pub(crate) const PHASE_DRAW_VISUAL_OVERRIDES: u32 = 13;
pub(crate) const PHASE_DRAW_TRANSITIONS: u32 = 14;
pub(crate) const PHASE_DRAW_ACTORS: u32 = 15;
pub(crate) const PHASE_DRAW_WORLD_OVERLAYS: u32 = 16;
pub(crate) const PHASE_DRAW_HUD: u32 = 17;
pub(crate) const PHASE_DRAW_WORLD_MAP: u32 = 18;
pub(crate) const PHASE_DRAW_INVENTORY: u32 = 19;
pub(crate) const PHASE_DRAW_NOTIFICATIONS: u32 = 20;

pub(crate) const CLIFF_STAGE_NONE: u32 = 0;
pub(crate) const CLIFF_STAGE_CELL_LOOKUP: u32 = 1;
pub(crate) const CLIFF_STAGE_RECIPE_RESOLVE: u32 = 2;
pub(crate) const CLIFF_STAGE_RAMP_OWNERSHIP: u32 = 3;
pub(crate) const CLIFF_STAGE_CONNECTOR_RESOLVE: u32 = 4;
pub(crate) const CLIFF_STAGE_BASE_DRAW: u32 = 5;
pub(crate) const CLIFF_STAGE_CONNECTOR_ART: u32 = 6;
pub(crate) const CLIFF_STAGE_SIDE_WATERFALL: u32 = 7;
pub(crate) const CLIFF_STAGE_WATER_VALLEY: u32 = 8;

static LAST_PHASE: AtomicU32 = AtomicU32::new(PHASE_BOOT);
static MAIN_THREAD_ID: AtomicU32 = AtomicU32::new(0);
static LAST_CLIFF_X: AtomicI32 = AtomicI32::new(i32::MIN);
static LAST_CLIFF_Y: AtomicI32 = AtomicI32::new(i32::MIN);
static LAST_CLIFF_FACE_SEGMENTS: AtomicU32 = AtomicU32::new(0);
static LAST_CLIFF_STAGE: AtomicU32 = AtomicU32::new(CLIFF_STAGE_NONE);
static CRASH_PATHS: OnceLock<NativeCrashPaths> = OnceLock::new();

struct NativeCrashPaths {
    dump_path_wide: Vec<u16>,
    report_path_wide: Vec<u16>,
    latest_path_wide: Vec<u16>,
    dump_display: String,
}

#[repr(C)]
struct ExceptionRecord {
    exception_code: u32,
    exception_flags: u32,
    exception_record: *mut ExceptionRecord,
    exception_address: *mut c_void,
    number_parameters: u32,
    exception_information: [usize; 15],
}

#[repr(C)]
struct ExceptionPointers {
    exception_record: *mut ExceptionRecord,
    context_record: *mut c_void,
}

#[repr(C)]
struct MiniDumpExceptionInformation {
    thread_id: u32,
    exception_pointers: *mut ExceptionPointers,
    client_pointers: i32,
}

type Handle = *mut c_void;
type UnhandledExceptionFilter = Option<unsafe extern "system" fn(*mut ExceptionPointers) -> i32>;

#[link(name = "kernel32")]
extern "system" {
    fn SetUnhandledExceptionFilter(filter: UnhandledExceptionFilter) -> UnhandledExceptionFilter;
    fn SetThreadStackGuarantee(stack_size_in_bytes: *mut u32) -> i32;
    fn GetCurrentProcess() -> Handle;
    fn GetCurrentProcessId() -> u32;
    fn GetCurrentThreadId() -> u32;
    fn CreateFileW(
        file_name: *const u16,
        desired_access: u32,
        share_mode: u32,
        security_attributes: *const c_void,
        creation_disposition: u32,
        flags_and_attributes: u32,
        template_file: Handle,
    ) -> Handle;
    fn WriteFile(
        file: Handle,
        buffer: *const c_void,
        bytes_to_write: u32,
        bytes_written: *mut u32,
        overlapped: *mut c_void,
    ) -> i32;
    fn CloseHandle(object: Handle) -> i32;
}

#[link(name = "dbghelp")]
extern "system" {
    fn MiniDumpWriteDump(
        process: Handle,
        process_id: u32,
        file: Handle,
        dump_type: u32,
        exception_param: *const MiniDumpExceptionInformation,
        user_stream_param: *const c_void,
        callback_param: *const c_void,
    ) -> i32;
}

pub(crate) fn install() {
    let logs = crate::runtime_config::runtime_root().join("logs");
    let crashes = logs.join("crashes");
    let _ = std::fs::create_dir_all(&crashes);
    let timestamp = crate::client_session_timestamp();
    let dump_path = crashes.join(format!("haven_game_native_{timestamp}.dmp"));
    let report_path = crashes.join(format!("haven_game_native_{timestamp}.txt"));
    let latest_path = logs.join("LATEST_CLIENT_CRASH.txt");
    let paths = NativeCrashPaths {
        dump_path_wide: wide_path(&dump_path),
        report_path_wide: wide_path(&report_path),
        latest_path_wide: wide_path(&latest_path),
        dump_display: dump_path.display().to_string(),
    };
    let _ = CRASH_PATHS.set(paths);

    // Reserve emergency stack space so the unhandled filter can still execute
    // after STATUS_STACK_OVERFLOW (0xC00000FD).
    let mut stack_guarantee = 64u32 * 1024;
    unsafe {
        let _ = SetThreadStackGuarantee(&mut stack_guarantee);
        MAIN_THREAD_ID.store(GetCurrentThreadId(), Ordering::Relaxed);
        let _ = SetUnhandledExceptionFilter(Some(native_exception_filter));
    }
    set_phase(PHASE_BOOT);
}

pub(crate) fn dump_candidate_path() -> Option<&'static str> {
    CRASH_PATHS.get().map(|paths| paths.dump_display.as_str())
}

#[inline]
pub(crate) fn set_phase(phase: u32) {
    LAST_PHASE.store(phase, Ordering::Relaxed);
}

#[inline]
pub(crate) fn set_cliff_context(global_x: i32, global_y: i32, face_segments: u8) {
    LAST_CLIFF_X.store(global_x, Ordering::Relaxed);
    LAST_CLIFF_Y.store(global_y, Ordering::Relaxed);
    LAST_CLIFF_FACE_SEGMENTS.store(u32::from(face_segments), Ordering::Relaxed);
}

#[inline]
pub(crate) fn set_cliff_stage(stage: u32) {
    LAST_CLIFF_STAGE.store(stage, Ordering::Relaxed);
}

unsafe extern "system" fn native_exception_filter(exception: *mut ExceptionPointers) -> i32 {
    let Some(paths) = CRASH_PATHS.get() else {
        return EXCEPTION_EXECUTE_HANDLER;
    };

    let exception_code = if !exception.is_null() && !(*exception).exception_record.is_null() {
        (*(*exception).exception_record).exception_code
    } else {
        0
    };
    let phase = LAST_PHASE.load(Ordering::Relaxed);
    let fault_thread_id = GetCurrentThreadId();
    let main_thread_id = MAIN_THREAD_ID.load(Ordering::Relaxed);
    let fault_on_main_thread = main_thread_id != 0 && fault_thread_id == main_thread_id;

    write_native_marker(
        &paths.report_path_wide,
        exception_code,
        phase,
        fault_on_main_thread,
    );
    write_native_marker(
        &paths.latest_path_wide,
        exception_code,
        phase,
        fault_on_main_thread,
    );

    let dump_file = CreateFileW(
        paths.dump_path_wide.as_ptr(),
        GENERIC_WRITE,
        0,
        std::ptr::null(),
        CREATE_ALWAYS,
        FILE_ATTRIBUTE_NORMAL,
        std::ptr::null_mut(),
    );
    if !is_invalid_handle(dump_file) {
        let exception_info = MiniDumpExceptionInformation {
            thread_id: GetCurrentThreadId(),
            exception_pointers: exception,
            client_pointers: 0,
        };
        let dump_type = MINI_DUMP_WITH_HANDLE_DATA
            | MINI_DUMP_WITH_UNLOADED_MODULES
            | MINI_DUMP_WITH_THREAD_INFO;
        let _ = MiniDumpWriteDump(
            GetCurrentProcess(),
            GetCurrentProcessId(),
            dump_file,
            dump_type,
            &exception_info,
            std::ptr::null(),
            std::ptr::null(),
        );
        let _ = CloseHandle(dump_file);
    }

    EXCEPTION_EXECUTE_HANDLER
}

unsafe fn write_native_marker(
    path: &[u16],
    exception_code: u32,
    phase: u32,
    fault_on_main_thread: bool,
) {
    let file = CreateFileW(
        path.as_ptr(),
        GENERIC_WRITE,
        0,
        std::ptr::null(),
        CREATE_ALWAYS,
        FILE_ATTRIBUTE_NORMAL,
        std::ptr::null_mut(),
    );
    if is_invalid_handle(file) {
        return;
    }

    write_bytes(file, b"Havenwild native client crash\r\n");
    write_bytes(file, exception_label(exception_code));
    write_bytes(
        file,
        if fault_on_main_thread {
            b"fault_thread_role=main\r\n"
        } else {
            b"fault_thread_role=background\r\n"
        },
    );
    write_bytes(file, phase_label(phase));
    if phase == PHASE_DRAW_STRUCTURAL_CLIFFS {
        let cliff_x = LAST_CLIFF_X.load(Ordering::Relaxed);
        let cliff_y = LAST_CLIFF_Y.load(Ordering::Relaxed);
        let face_segments = LAST_CLIFF_FACE_SEGMENTS.load(Ordering::Relaxed);
        let cliff_stage = LAST_CLIFF_STAGE.load(Ordering::Relaxed);
        if cliff_x != i32::MIN && cliff_y != i32::MIN {
            write_i32_field(file, b"cliff_global_x=", cliff_x);
            write_i32_field(file, b"cliff_global_y=", cliff_y);
            write_u32_field(file, b"cliff_face_segments=", face_segments);
        }
        write_bytes(file, cliff_stage_label(cliff_stage));
    }
    write_bytes(file, b"A Windows minidump was requested for this crash.\r\n");
    let _ = CloseHandle(file);
}

unsafe fn write_bytes(file: Handle, bytes: &[u8]) {
    let mut written = 0u32;
    let _ = WriteFile(
        file,
        bytes.as_ptr().cast(),
        bytes.len().min(u32::MAX as usize) as u32,
        &mut written,
        std::ptr::null_mut(),
    );
}


unsafe fn write_i32_field(file: Handle, prefix: &[u8], value: i32) {
    write_bytes(file, prefix);
    let mut buffer = [0u8; 16];
    let len = encode_i64_decimal(i64::from(value), &mut buffer);
    write_bytes(file, &buffer[..len]);
    write_bytes(file, b"
");
}

unsafe fn write_u32_field(file: Handle, prefix: &[u8], value: u32) {
    write_bytes(file, prefix);
    let mut buffer = [0u8; 16];
    let len = encode_i64_decimal(i64::from(value), &mut buffer);
    write_bytes(file, &buffer[..len]);
    write_bytes(file, b"
");
}

fn encode_i64_decimal(value: i64, out: &mut [u8; 16]) -> usize {
    let negative = value < 0;
    let mut magnitude = value.unsigned_abs();
    let mut reverse = [0u8; 16];
    let mut count = 0usize;
    if magnitude == 0 {
        reverse[count] = b'0';
        count += 1;
    } else {
        while magnitude > 0 && count < reverse.len() {
            reverse[count] = b'0' + (magnitude % 10) as u8;
            magnitude /= 10;
            count += 1;
        }
    }
    let mut cursor = 0usize;
    if negative {
        out[cursor] = b'-';
        cursor += 1;
    }
    for index in (0..count).rev() {
        out[cursor] = reverse[index];
        cursor += 1;
    }
    cursor
}

fn cliff_stage_label(stage: u32) -> &'static [u8] {
    match stage {
        CLIFF_STAGE_CELL_LOOKUP => b"cliff_stage=cell_lookup\r\n",
        CLIFF_STAGE_RECIPE_RESOLVE => b"cliff_stage=recipe_resolve\r\n",
        CLIFF_STAGE_RAMP_OWNERSHIP => b"cliff_stage=ramp_ownership\r\n",
        CLIFF_STAGE_CONNECTOR_RESOLVE => b"cliff_stage=connector_resolve\r\n",
        CLIFF_STAGE_BASE_DRAW => b"cliff_stage=base_draw\r\n",
        CLIFF_STAGE_CONNECTOR_ART => b"cliff_stage=connector_art\r\n",
        CLIFF_STAGE_SIDE_WATERFALL => b"cliff_stage=side_waterfall\r\n",
        CLIFF_STAGE_WATER_VALLEY => b"cliff_stage=water_valley\r\n",
        _ => b"cliff_stage=none_or_unclassified\r\n",
    }
}

fn exception_label(code: u32) -> &'static [u8] {
    match code {
        EXCEPTION_STACK_OVERFLOW => b"exception=stack_overflow (0xC00000FD)\r\n",
        EXCEPTION_ACCESS_VIOLATION => b"exception=access_violation (0xC0000005)\r\n",
        _ => b"exception=other_windows_exception\r\n",
    }
}

fn phase_label(phase: u32) -> &'static [u8] {
    match phase {
        PHASE_LIVE_BRIDGE => b"phase=development_live_bridge\r\n",
        PHASE_UPDATE => b"phase=game_update\r\n",
        PHASE_APPEARANCE_RELOAD => b"phase=character_appearance_reload\r\n",
        PHASE_DRAW => b"phase=game_draw\r\n",
        PHASE_PAUSE_DRAW => b"phase=pause_menu_draw\r\n",
        PHASE_PRESENT => b"phase=frame_present\r\n",
        PHASE_TELEMETRY => b"phase=frame_telemetry\r\n",
        PHASE_SNAPSHOT => b"phase=performance_snapshot\r\n",
        PHASE_RUNTIME_EXIT => b"phase=runtime_exit_persistence\r\n",
        PHASE_DRAW_CLEAR => b"phase=draw_clear_and_camera\r\n",
        PHASE_DRAW_MAP => b"phase=draw_map\r\n",
        PHASE_DRAW_STRUCTURAL_CLIFFS => b"phase=draw_structural_cliffs\r\n",
        PHASE_DRAW_VISUAL_OVERRIDES => b"phase=draw_visual_overrides\r\n",
        PHASE_DRAW_TRANSITIONS => b"phase=draw_transitions\r\n",
        PHASE_DRAW_ACTORS => b"phase=draw_actors_buildings_player\r\n",
        PHASE_DRAW_WORLD_OVERLAYS => b"phase=draw_world_overlays\r\n",
        PHASE_DRAW_HUD => b"phase=draw_hud_and_ui\r\n",
        PHASE_DRAW_WORLD_MAP => b"phase=draw_world_map\r\n",
        PHASE_DRAW_INVENTORY => b"phase=draw_inventory_crafting\r\n",
        PHASE_DRAW_NOTIFICATIONS => b"phase=draw_processing_notifications\r\n",
        _ => b"phase=boot_or_unclassified\r\n",
    }
}

fn is_invalid_handle(handle: Handle) -> bool {
    handle.is_null() || handle as isize == -1
}

fn wide_path(path: &std::path::Path) -> Vec<u16> {
    use std::os::windows::ffi::OsStrExt;
    path.as_os_str().encode_wide().chain(Some(0)).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn known_native_exception_and_phase_labels_are_stable() {
        assert_eq!(
            exception_label(EXCEPTION_STACK_OVERFLOW),
            b"exception=stack_overflow (0xC00000FD)\r\n"
        );
        assert_eq!(phase_label(PHASE_UPDATE), b"phase=game_update\r\n");
        assert_eq!(phase_label(PHASE_DRAW), b"phase=game_draw\r\n");
        assert_eq!(
            phase_label(PHASE_DRAW_INVENTORY),
            b"phase=draw_inventory_crafting\r\n"
        );
        assert_eq!(
            cliff_stage_label(CLIFF_STAGE_RAMP_OWNERSHIP),
            b"cliff_stage=ramp_ownership\r\n"
        );
        let mut buffer = [0u8; 16];
        let len = encode_i64_decimal(-4096, &mut buffer);
        assert_eq!(&buffer[..len], b"-4096");
    }
}
