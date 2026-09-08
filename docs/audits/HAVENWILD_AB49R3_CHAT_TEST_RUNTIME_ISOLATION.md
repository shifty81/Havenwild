# H21A14AB49R3 — Chat Test Runtime Isolation

The AB49R2 Windows gate compiled successfully and reached the Havenwild game tests. The only remaining failure was `runtime_chat::tests::chat_history_is_bounded`, which called `RuntimeChatState::push_message()`. That runtime method updates activity time through Macroquad `get_time()`, but ordinary Rust unit tests do not run inside Macroquad's initialized main-thread context.

R3 separates deterministic history mutation from the runtime clock:

- `push_message_at(message, activity_at)` owns bounded history + activity timestamp mutation.
- normal gameplay `push_message(message)` still obtains `get_time()` and delegates to the deterministic helper.
- the unit test supplies an explicit timestamp, so it validates the bounded-history contract without requiring a graphics/runtime context.

No player-facing chat behavior, HUD placement, input flow, rendering, or history size is changed.
