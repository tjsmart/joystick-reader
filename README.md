joystick-reader
===============

A simple GUI for reading and plotting joystick motion in real time. 🎮

I wrote this as fun side project to test my controller joysticks. 🙌


## Installation 🔽

```bash
pipx install git+https://github.com/tjsmart/joystick-reader
```

## Running 🏃

```bash
joystick-reader
```

## Example 🤓

Below is an example output from four N64 joysticks. I've noticed
some issues getting full output on the up motion on the red joystick
which is confirmed by the plot below.

![](./example.png)


## Trouble shooting 🥴

`joystick-reader` assumes that the joystick will be in the first slot
that `pygame` detects. If you are using an adapter with multiple slots
or have multiple controllers connected, try using a different slot.
