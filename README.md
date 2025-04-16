
INGV CASSANDRA PROJECT
======================

Cassandra Manager is an internal toolkit developed for the INGV Experimental VLF Network.

It provides a modern interface to:

- View LoRes (hourly) and HiRes (~40s) spectrograms
- Explore and play waveform audio files (.wav)
- Simulate and eventually perform AI-based signal detection
- Download data files for offline inspection

--------------------------------------------
PROJECT STRUCTURE
--------------------------------------------

- parser/           -> Filename parsers and file managers  
- tests/            -> Unit tests for parsing and indexing logic  
- UI/               -> Streamlit-based interactive user interface  
- requirements.txt  -> Python dependencies  
- Makefile          -> Developer commands using Docker  

--------------------------------------------
HOW TO RUN
--------------------------------------------

You can build and run the project using Docker and the Makefile.

1. **Build the development container**  
```bash
make build
```

2. **Run the application**  
```bash
make dev
```

3. **Run unit tests**  
```bash
make test
```

5. **Run linter**  
```bash
make check
```

5. **Build the UI**  
```bash
make show
```


Note: If port 8501 is already used, change the port mapping in the Makefile.

--------------------------------------------
THEORETICAL AI INTEGRATION
--------------------------------------------

In the final version, AI will perform continuous inference on new WAV files.
When a signal of interest is found:

- The corresponding spectrograms can be reviewed immediately
- Logs will display detection events
- Users can download and analyze flagged data

Currently, AI inference is simulated via a stub system in the UI.

--------------------------------------------
UI OVERVIEW
--------------------------------------------

The interface has 3 main tabs:

1. Spectrograms
   - Visualize LoRes and HiRes images by time
   - Choose between time slider or hour-based navigation
   - HiRes view can be expanded with a custom window (+/- minutes)

2. Waveform + AI
   - Select and zoom into .wav files
   - Listen to audio and simulate inference using mocked models

3. Logs
   - Shows runtime logs and inference feedback
   - Includes status levels: GREEN (info), YELLOW (warning), RED (errors)

Controls such as time range, station, and source/target folders are available
in the sidebar and affect all tabs.

--------------------------------------------
DOWNLOAD OPTIONS
--------------------------------------------

From the UI sidebar, users can:

- Download all files
- Download only WAV files
- Download only spectrograms
- Filter by LoRes or HiRes
- Define output folders

--------------------------------------------
COMING SOON
--------------------------------------------

- SSH-based remote file fetching from VLF stations
- AI integration with real neural networks (1D CNN, RNN, etc.) and continuous inference
- Export of detection results and logs
