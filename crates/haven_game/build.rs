fn main() {
    let target_os = std::env::var("CARGO_CFG_TARGET_OS").unwrap_or_default();
    let target_env = std::env::var("CARGO_CFG_TARGET_ENV").unwrap_or_default();
    if target_os == "windows" && target_env == "msvc" {
        // Macroquad/miniquad runs Havenwild's renderer on the process main thread.
        // Reserve a normal game-sized stack so finite debug/render call depth has
        // headroom. Infinite recursion still fails and is separately attributed by
        // native_crash_windows; this is not used as a recursion workaround.
        println!("cargo:rustc-link-arg=/STACK:8388608");
    }
}
