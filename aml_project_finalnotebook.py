# -*- coding: utf-8 -*-
"""AML_Project_FinalNotebook.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/github/Darsangmdd/AML-project/blob/main/archive/AML_Project_FinalNotebook.ipynb

### Pre-Processing and Exploratory Data Analysis
"""

from google.colab import drive
drive.mount('/content/drive')

# Commented out IPython magic to ensure Python compatibility.
# Import Libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
import seaborn as sns
from tqdm.notebook import tqdm
import pickle
import warnings
import spacy
import nltk
import regex as re
from nltk.corpus import stopwords
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from textblob import TextBlob, Word
from sklearn.feature_extraction.text import CountVectorizer
import plotly.express as px
from collections import Counter
from string import punctuation
from nltk.tokenize import word_tokenize
warnings.filterwarnings('ignore')
from sklearn.svm import LinearSVC
from sklearn.pipeline import make_pipeline
from imblearn.pipeline import make_pipeline as make_imbal_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import make_classification
from sklearn.metrics import classification_report, confusion_matrix,accuracy_score, recall_score,plot_confusion_matrix
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.calibration import CalibratedClassifierCV, CalibrationDisplay
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from imblearn.over_sampling import SMOTE
from sklearn.metrics import f1_score
from keras.models import Sequential
import tensorflow as tf
from keras.layers import *

# %matplotlib inline

# Read df
df = pd.read_csv('/content/drive/MyDrive/AML Project/mbti_1.csv')

# Global Vars
nltk.download('stopwords')
nltk.download('punkt')
nlp = spacy.load("en_core_web_sm")
cachedStopWords = stopwords.words("english")
types = df['type'].tolist()
set_types = set([i.lower() for i in types])
print(set_types)

"""#### Text Pre-processing & Cleaning"""

#function to remove stop words like the, is, a..etc

def remove_stop(row):
  global cachedStopWords
  global set_types

  row = ' '.join([word for word in row.split() if word not in cachedStopWords])
  row = ' '.join([word for word in row.split() if word not in set_types])
  return row

#function to perform lemmatization 

def lemmatize(row):
  doc = nlp(row)
  return ' '.join([token.lemma_ for token in doc])

#function to get the keywords from the posts

def get_keywords(text):
    keywords = []
    pos_tag = ['PROPN', 'ADJ', 'NOUN'] 
    doc = nlp(text) 
    for token in doc:

        if(token.text in punctuation):
            keywords.append(token.text)

        if(token.pos_ in pos_tag):
            keywords.append(token.text)
    return ' '.join(word for word in keywords)

#remove unwanted spaces

def remove_unwanted_space(text):
    val1 = '.'
    sentences = text.split('.')
    updated_sentences = []
    for sentence in sentences:
        updated_sentences.append(sentence.strip())
    try:
        while True:
            updated_sentences.remove(val1)
    except ValueError:
        pass
    val2 = ''
    try:
        while True:
            updated_sentences.remove(val2)
    except ValueError:
        pass
    updated_text = ". ".join(updated_sentences)
    return updated_text

#main function which peforms all the text pre-processing

def process_text(df):

  df['posts'] = df['posts'].apply(lambda x: x.lower())
  df['posts'] = df['posts'].apply(lambda x: re.sub(r'http\S+', '', x))
  df['posts'] = df['posts'].apply(lambda x: x.replace("'", ""))

  df['posts'] = df['posts'].apply(lambda x: re.sub(r'[^ a-z\.]+', '', x))
  df['posts'] = df['posts'].apply(lambda x: remove_stop(x))
  df['posts'] = df['posts'].apply(lambda x: lemmatize(x))
  df['posts'] = df['posts'].apply(lambda x: get_keywords(x))
  df['posts'] = df['posts'].apply(lambda x: remove_unwanted_space(x))
  return df

df = process_text(df)

"""#### Word Vector Embeddings"""

!wget http://nlp.stanford.edu/data/glove.6B.zip
!unzip glove*.zip
!ls
!pwd
print('Indexing word vectors.')

embeddings_index = {}
f = open('glove.6B.100d.txt', encoding='utf-8')
for line in f:
    values = line.split()
    word = values[0]
    coefs = np.asarray(values[1:], dtype='float32')
    embeddings_index[word] = coefs
f.close()

print('Found %s word vectors.' % len(embeddings_index))

#Functions to convert words into vectors

def do_embedding(row):
  vector_list = []
  for word in row:
    try:
      vector_list.append(embeddings_index[word])
    except:
      pass
  return vector_list

def word_embeddings(df):
  df['vectors'] = df['posts'].apply(lambda x: do_embedding(x))
  return df

# Save df
vectorized_df = word_embeddings(df)

print(len(df), len(vectorized_df))
vectorized_df

df = vectorized_df

"""#### EDA"""

data = vectorized_df

x = data.type.value_counts()
plt.figure(figsize=(10,6))
ax = sns.barplot(x.index, x.values, alpha=0.8)
plt.title('The Distribution of Different Personality Types')
plt.ylabel('Count')
plt.xlabel('MBTI Types')
rects = ax.patches
labels = x.values
for rect, label in zip(rects, labels):
    height = rect.get_height()
    ax.text(rect.get_x() + rect.get_width()/2, height + 5, label, ha='center', va='bottom')
plt.show();

#calculating the polarity scores of every post to understand sentiment

data['polarity'] = data['posts'].map(lambda x:TextBlob(x).sentiment.polarity)

x = round(data.groupby('type')['polarity'].mean(), 2)
plt.figure(figsize=(10,6))
ax = sns.barplot(x.index, x.values, alpha=0.8)
plt.title("MBTI_TYPES AVERAGE SENTIMENT")
plt.ylabel('MEAN POLARITY')
plt.xlabel('MBTI_TYPES')
plt.show()

#calculating the subjectivity scores of every post to understand the difference between fact/opinion

data['subjectivity'] = data['posts'].map(lambda x:TextBlob(x).sentiment.subjectivity)

x = round(data.groupby('type')['subjectivity'].mean(), 2)
plt.figure(figsize=(10,6))
ax = sns.barplot(x.index, x.values, alpha=0.8)
plt.title("MBTI_TYPES AVERAGE SENTIMENT")
plt.ylabel('MEAN SUBJECTIVITY')
plt.xlabel('MBTI_TYPES')
plt.show()

def generate_wordcloud(text, title):
    # Create and generate a word cloud image:
    wordcloud = WordCloud(background_color="white").generate(text)

    # Display the generated image:
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.title(title, fontsize = 40)
    plt.show()

df_by_personality = data.groupby("type")['posts'].apply(' '.join).reset_index()

#Generating word clouds and histograms to understand the most commonly used words for each personality type

fig, ax = plt.subplots(len(data['type'].unique()), sharex=True, figsize=(15,10*len(data['type'].unique())))

k = 0
for i in data['type'].unique():
    df_4 = data[data['type'] == i]
    wordcloud = WordCloud().generate(df_4['posts'].to_string())
    ax[k].imshow(wordcloud)
    ax[k].set_title(i)
    ax[k].axis("off")
    k+=1

for i in data['type'].unique():
    cv = CountVectorizer(stop_words = 'english')
    words = cv.fit_transform(data[data['type'] == i].posts)
    sum_words = words.sum(axis=0)


    words_freq = [(word, sum_words[0, idx]) for word, idx in cv.vocabulary_.items()]
    words_freq = sorted(words_freq, key = lambda x: x[1], reverse = True)
    frequency = pd.DataFrame(words_freq, columns=['word', 'freq'])

    plt.style.use('fivethirtyeight')
    color = plt.cm.ocean(np.linspace(0, 1, 20))
    frequency.head(20).plot(x='word', y='freq', kind='bar', figsize=(15, 6), color = color)
    plt.title("20 Most Frequently used words by {} personality type".format(i))
    plt.show()

px.pie(data,names='type',title='PERSONALITY TYPE',hole=0.3)

data['word_count'] = data['posts'].apply(lambda x: len(x.split()))
data['char_count'] = data['posts'].apply(len)

#Understanding the distribution of Word counts for each personality type

for i in data['type'].unique():
    sns.histplot(data=data[data['type'] == i]['word_count'], kde=True)
    plt.title("{} Personality Type".format(i), fontsize=15)
    plt.xlabel('Words', fontsize=10)
    plt.ylabel('Count', fontsize=10)
    plt.show()

#Understanding the distribution of Character counts for each personality type

for i in data['type'].unique():
    sns.histplot(data=data[data['type'] == i]['char_count'], kde=True)
    plt.title("{} Personality Type".format(i), fontsize=15)
    plt.xlabel('Characters', fontsize=10)
    plt.ylabel('Count', fontsize=10)
    plt.show()

"""### Split data by categories"""

# Get average of vectors
df1 = pd.DataFrame([],columns=range(100))
for i in tqdm(range(len(df))):
    vec = sum(df['vectors'][i])/len(df['vectors'][1])
    df1.loc[len(df1)] = vec

df1['type'] = df['type']

display(df1)

### SPLIT BY CATEGORIES
ie = ['I', 'E']
sn = ['S', 'N']
tf = ['T', 'F']
jp = ['J', 'P']

print(len(df1))

iedf = df1.copy()
iedf['type'] = df1['type'].apply(lambda x: [i for i in x if i in ie][0])


sndf = df1.copy()
sndf['type'] = df1['type'].apply(lambda x: [i for i in x if i in sn][0])


tfdf = df1.copy()
tfdf['type'] = df1['type'].apply(lambda x: [i for i in x if i in tf][0])


jpdf = df1.copy()
jpdf['type'] = df1['type'].apply(lambda x: [i for i in x if i in jp][0])

# Example Output
jpdf.head(3)

# Convert chars to 1 or 0 to allow for classification
iedf['type'] = iedf['type'].replace(list(set(iedf['type'])),range(len(list(set(iedf['type'])))))
sndf['type'] = sndf['type'].replace(list(set(sndf['type'])),range(len(list(set(sndf['type'])))))
tfdf['type'] = tfdf['type'].replace(list(set(tfdf['type'])),range(len(list(set(tfdf['type'])))))
jpdf['type'] = jpdf['type'].replace(list(set(jpdf['type'])),range(len(list(set(jpdf['type'])))))

iedf.head(3)

sndf.head(3)

tfdf.head(3)

jpdf.head(3)

"""### Train ML Models"""

def get_SVC(X_dev, y_dev, X_test, y_test):
  
  svc_model1=LinearSVC(loss='hinge',  random_state=42)
  smote = SMOTE(random_state=42)
  smote.fit_resample(X_dev, y_dev)
  pipe_svc = make_imbal_pipeline(smote, GridSearchCV(LinearSVC(random_state = 42),
                                  param_grid={'max_iter': [25, 50, 100, 150],
                                              'C': [0.01, 0.1, 0.5, 0.7, 1, 3]},
                                  cv=5,
                                  scoring='f1_micro',
                                  refit=True))
    
  results = pipe_svc.fit(X_dev, y_dev)
  preds = pipe_svc.predict(X_test)
  print(f1_score(y_test, preds, average='micro'))
  

  return preds

def get_RF(X_dev, y_dev, X_test, y_test):
  smote = SMOTE(random_state=42)
  smote.fit_resample(X_dev, y_dev)
  pipe_rfc = make_imbal_pipeline(smote, GridSearchCV(RandomForestClassifier(random_state = 42),
                                  param_grid={'ccp_alpha': [0.1, 0.2, 0.3],
                                              'n_estimators': [25, 50, 75],
                                              'max_depth': [3, 5, 7]},
                                  cv = 5,
                                  scoring='f1_micro',
                                  refit = True))
  results = pipe_rfc.fit(X_dev, y_dev)
  preds = pipe_rfc.predict(X_test)
  print(f1_score(y_test, preds, average='micro'))

  
  return preds

def get_HGB(X_dev, y_dev, X_test, y_test):

  smote = SMOTE(random_state=42)
  smote.fit_resample(X_dev, y_dev)
  pipe_hgbc = make_imbal_pipeline(smote, GridSearchCV(HistGradientBoostingClassifier(random_state=33),
                                  param_grid={'learning_rate': [0.1, 0.2, 0.3],
                                              'max_iter': [25, 50, 100],
                                              'max_depth': [3, 5, 7]},
                                  cv=5,
                                  scoring='f1_micro',
                                  refit=True))
    
  results = pipe_hgbc.fit(X_dev, y_dev)
  preds = pipe_hgbc.predict(X_test)
  print(f1_score(y_test, preds, average='micro'))

  X_train, X_calib, y_train, y_calib = train_test_split(X_dev, y_dev, test_size=0.2, random_state=19)

  cal_hgb_platt = CalibratedClassifierCV(pipe_hgbc, cv='prefit', method='sigmoid')
  cal_hgb_platt.fit(X_calib, y_calib)
  
  cal_preds = cal_hgb_platt.predict(X_test)
  print(f1_score(y_test, cal_preds, average='micro'))
  return preds, cal_preds

def get_KNN(X_dev, y_dev, X_test, y_test):
  smote = SMOTE(random_state=42)
  smote.fit_resample(X_dev, y_dev)

  pipe_KNN = make_imbal_pipeline(smote, GridSearchCV(KNeighborsClassifier(n_jobs=-1),
                                  param_grid={'n_neighbors': list(range(1, 31))},
                                  cv = 10,
                                  scoring='f1_micro',
                                  refit = True))

  results = pipe_KNN.fit(X_dev, y_dev)

  preds = pipe_KNN.predict(X_test)
  print(f1_score(y_test, preds, average='micro'))


  return preds

def get_LR(X_dev, y_dev, X_test, y_test):

  smote = SMOTE(random_state=42)
  smote.fit_resample(X_dev, y_dev)
  lr=LogisticRegression(random_state=0)
  solvers = ['newton-cg', 'lbfgs', 'liblinear']
  penalty = ['l2']
  c_values = [100, 10, 1.0, 0.1, 0.01]
  grid = dict(solver=solvers,penalty=penalty,C=c_values)
  cv = 10
  pipe_lr = make_imbal_pipeline(smote,  GridSearchCV(estimator=lr, param_grid=grid, n_jobs=-1, cv=cv, scoring='f1_micro'))  
  results = pipe_lr.fit(X_dev, y_dev)
  preds = pipe_lr.predict(X_test)
  print(f1_score(y_test, preds, average='micro'))
  return preds

def get_NB(X_dev, y_dev, X_test, y_test):

  smote = SMOTE(random_state=42)
  smote.fit_resample(X_dev, y_dev)
  gnb = GaussianNB()
  params_NB = {'var_smoothing': np.logspace(0,-9, num=100)}
  pipe_nb = make_imbal_pipeline(smote, GridSearchCV(gnb,
                                  param_grid=params_NB,
                                  cv=5,
                                  scoring='f1_micro',
                                  refit=True))
    
  results = pipe_nb.fit(X_dev, y_dev)
  preds = pipe_nb.predict(X_test)
  print(f1_score(y_test, preds, average='micro'))
  return preds

# Run Models for each 

char_list = ['IE', 'SN', 'TF', 'JP']

df_li = [iedf, sndf, tfdf, jpdf]
df_dict = dict()

# For each pair of characteristics
for i in range(len(df_li)):

  

  # Get the raw df
  dataframe = df_li[i]

  X = dataframe.drop('type', axis=1)
  y = dataframe['type']

  # First split into dev and test
  X_dev, X_test, y_dev, y_test = train_test_split(X, y, 
                                                    test_size = 0.25,
                                                    stratify=y,
                                                    random_state = 42)

  # Run Classification Models
  print(char_list[i])
  svc_preds = get_SVC(X_dev, y_dev, X_test, y_test)
  rf_preds = get_RF(X_dev, y_dev, X_test, y_test)
  hgb_preds, cal_hgb_preds = get_HGB(X_dev, y_dev, X_test, y_test)
  KNN_preds = get_KNN(X_dev, y_dev, X_test, y_test)
  lr_preds=get_LR(X_dev, y_dev, X_test, y_test)
  nb_preds=get_NB(X_dev, y_dev, X_test, y_test)
  
  
  # Print Results of Classification models
  
  print("SVC")
  print(classification_report(y_test,svc_preds))
  print("Random Forest")
  print(classification_report(y_test,rf_preds))
  print("HistGradientBoost")
  print(classification_report(y_test,hgb_preds))
  print("CalibratedHistGB")
  print(classification_report(y_test,cal_hgb_preds))
  print('KNN')
  print(classification_report(y_test,KNN_preds))
  print("Logistic Regression")
  print(classification_report(y_test,lr_preds))
  print("Naive Bayes")
  print(classification_report(y_test,nb_preds))

"""### Train Deep Learning Models: RNN (LSTM)"""

char_list = ['IE', 'SN', 'TF', 'JP']

df_li = [iedf, sndf, tfdf, jpdf]
df_dict = dict()

# For each pair of characteristics
for i in range(len(df_li)):

  

  # Get the raw df
  dataframe = df_li[i]

  X = dataframe.drop('type', axis=1)
  y = dataframe['type']


  # First split into dev and test
  X_dev, X_test, y_dev, y_test = train_test_split(X, y, 
                                                    test_size = 0.25,
                                                    stratify=y,
                                                    random_state = 42)
  
  X_train, X_val, y_train, y_val = train_test_split(X, y, 
                                                    test_size = 0.25,
                                                    random_state = 42)
  




  model = Sequential()
  model.add(LSTM(100, input_shape=(100,1), return_sequences=True))
  model.add(Bidirectional(LSTM(64, return_sequences=True)))
  model.add(Bidirectional(LSTM(64)))
  model.add(Dense(32, activation='relu'))
  model.add(Dense(1, activation='sigmoid'))
  model.compile("adam", "binary_crossentropy", metrics=['accuracy'])
  model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=20,batch_size=100, verbose=0)

  y_pred = model.predict(X_test, batch_size=64, verbose=1)
  y_pred_bool = np.argmax(y_pred, axis=1)

  print(classification_report(y_test, y_pred_bool))
  print(f1_score(y_test, y_pred_bool, average='micro'))

"""**Thank you!**"""