# Feishu

Outbound Feishu support is implemented as a shared notification helper.

It is designed to:

- work when configured
- fail open when disabled
- stay independent from the skill authoring layer

The main runtime command is `feishu-notify`.
