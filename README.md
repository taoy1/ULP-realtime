## Welcome to this repo

This repo provides an automation tool for creating real-time sensing ULP programs that can be run by ESP32 on PYCOM.

First create a top folder, for example:
```
mkdir ~/esp32
cd ~/esp32
```

Then clone the esp-idf and pycom repos forked and customized by taoy1:
```
git clone https://github.com/taoy1/pycom-esp-idf
git clone https://github.com/taoy1/pycom-micropython-sigfox
```

If you want to use our automation tool to generate ULP program for you, continue the next section 'Auto generate ULP program'. If you just want to use ULP on PYCOM and manually write your ULP program, jump to section 'Write your ULP program'. 

### Auto generate ULP program

In the top directory, git clone another repo:

```
git clone https://github.com/taoy1/ULP-realtime/
```

To get started, you can try an example ULP application configuration. The examples folder provides some example configurations. You can use use them to generate ULP program:

```
cd ULP-realtime
python ulp_realtime.py examples/adc_sum.json
```

This will generate main.c and ulp_realtime.S in the output folder.
Now jump to section 'Build the ESP32 components including ulp and ulptest' to build your ULP program.

### Write your ULP program

Enter esp-idf directory. Because you just want to write your own ULP program, go back to the commit with no automation.
```
cd pycom-esp-idf
git reset --hard 1f1cb1a
```
In this commit (1f1cb1a), we have created a ESP32 component called ulptest as directory components/ulptest.
If you change your mind, you can use ```git reset --hard 717a701``` to use the automation.

### Build the ESP32 components including ulp and ulptest

Return to the top folder. Because ESP32 needs to be built in a project folder, we have customized the hello_world project. Go to the hello-world project folder:

```
cd pycom-esp-idf/examples/get-started/hello_world/
```

Modify script micropython-copy.sh. Set the ESP_IDF_PATH and ESP32_PATH to your $TOP/pycom-esp-idf/ and $TOP/pycom-micropython-sigfox/esp32/. If you are using automation, also set the ULP_REALTIME_PATH to your $TOP/ulp-realtime. 

```
vi micropython-copy.sh
```

Then run the script. It will build all components inside the hello_world project, and copy sdkconfig and libraries (.a file) generated from components into $TOP/pycom-micropython-sigfox/esp32. If you are using automation, before everything the script copies your automation output from $ULP_REALTIME_PATH/output into $TOP/pycom-esp-idf/components/ulptest.

```
./micropython-copy.sh
```

If there's any error in building the ESP32, you haven't fully installed/configured the ESP32 or ULP toolchain. Refer to https://dl.espressif.com/doc/esp-idf/latest/get-started/linux-setup.html to setup toolchain for ESP-IDF. Refer to http://esp-idf.readthedocs.io/en/latest/api-guides/ulp.html to setup toolchain for ULP.

### Build PYCOM and flash

Return to the top folder. Enter pycom-micropython-sigfox's folder.

Before building ESP32, you need to build mpy-cross:
```
cd mpy-cross && make clean && make && cd -
```
Then enter PYCOM's ESP32 folder and build PYCOM, as instructed on https://github.com/taoy1/pycom-micropython-sigfox:

For example, to build LoPY for 868Hz regions:
```
make BOARD=LOPY TARGET=boot clean
make BOARD=LOPY TARGET=boot
make BOARD=LOPY LORA_BAND=USE_BAND_868 TARGET=app
```

Now, connect G23 to GND with a jump wire. Connect to computer and do
```
make BOARD=LOPY LORA_BAND=USE_BAND_868 flash
```


