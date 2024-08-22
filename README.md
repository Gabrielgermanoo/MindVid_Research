# MindVid_Research

## How it works?

* This is a Crawler made for Instagram Reels to extract data from very access videos;

## Project modules

* First step: Extract audio from videos with 100k or plus visualizations and grab the link of this Reels:
    *[Searching Videos of Reels]()

* Second step: With those videos downloaded, verifies if are people speech or other type of sound. If are people speech, the video is transcripted to a csv ready for made his classification;
    * At this point, send this csv file to specialists to made the classification.
    * [Audio Processor]()
* Third step: Now, making NLP tecniques for vectorize those text and use AI Models for training this data.
    * [NLP_Tokening]()
