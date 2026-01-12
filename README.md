# MindVid_Research

- Developed by: [Gabriel Germano](https://www.linkedin.com/in/gabriel-germano-867aa51b6/)

## How it works?

* This is a Crawler made for Instagram Reels to extract data from very access videos. After the data collector, the audio is processed to verify if there is people speech. If there is, the audio is transcribed to text and stored in a csv file for later classification. Finally, with the classified data, NLP techniques and AI models are used for training and analysis.

## Requirements

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (optional but recommended)
- Instagram account (for accessing Reels)
- FFmpeg (for audio extraction)
- Appium (for mobile automation)

## Installation

### Appium Setup

- Install Appium globally using npm:
  ```bash
  npm install -g appium
  ```
- Start the Appium server:
  ```bash
  appium
  ```
- If you need to use the appium inspector, you can install it via plugin:
  ```bash
    appium plugin install inspector
  ```
- Start the Appium server with the inspector:
  ```bash
    appium --use-plugins=inspector --allow-cors
  ```
- Start the appium via browser ( for a port 4723):
  ```bash
    http://localhost:4723/
  ```

### Python Environment Setup
- Create and activate a virtual environment (optional but recommended):
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows use `venv\Scripts\activate`
  ```
- Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
- After this, you already have all the dependencies installed and can run the project modules.

## Project modules

* First step: Extract audio from videos with 100k or plus visualizations and grab the link of this Reels or TikTok videos:
    *[Searching Videos of Reels]()
    *[Searching Videos of TikTok]()

* Second step: With those videos downloaded, verifies if are people speech or other type of sound. If are people speech, the video is transcripted to a csv ready for made his classification;
    * At this point, send this csv file to specialists to made the classification.
    * [Speech Recognition]()
    * [Audio Processor]()
* Third step: Now, making NLP tecniques for vectorize those text and use AI Models for training this data.
    * [NLP_Tokening]()
    * [AI_Models]()
  
## Notebooks

- In the `notebooks` directory, you will find Jupyter notebooks that demonstrate how to use the various modules of the project. These notebooks provide step-by-step instructions and examples. There is a notebook with the state of art models for text classification (used in the last step of the project).

## Contributing
- Contributions are welcome! Please fork the repository and create a pull request with your changes.