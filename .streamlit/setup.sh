#!/bin/bash

# 建立 nltk_data 資料夾（若不存在）
mkdir -p ~/.nltk_data

# 預先下載 NLTK 所需的資源
python -m nltk.downloader -d ~/.nltk_data punkt stopwords