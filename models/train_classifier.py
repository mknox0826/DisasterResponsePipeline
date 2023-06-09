# Import libraries

import sys
import nltk
nltk.download(['punkt', 'wordnet', 'averaged_perceptron_tagger'])

import re
import numpy as np
import pandas as pd
import pickle
from sqlalchemy import create_engine
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from sklearn.multioutput import MultiOutputClassifier
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer


def load_data(database_filepath):
    '''
    Load data from sqlite database
    
    Input:
    database_filpath - filepath to sqlite db where cleaned df is stored
    
    Output:
    X - feature variables
    Y - target variables
    category_names - names of message categories
   
    '''
    engine = create_engine('sqlite:///' + database_filepath)
  
    df = pd.read_sql_table("DisasterCleaned", engine)
    
    df = df.drop(columns=['child_alone'])
    X = df.message.values
    Y = df.iloc[:,4:]
    category_names = Y.columns
    
    
    return df, X, Y, category_names
    


def tokenize(text):
    '''
    Inputs: 
    text - message data
    
    Output: 
    clean_tokens - list of tokenized words 
    
    '''
    url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    
    # list of all urls using regex
    detected_urls = re.findall(url_regex, text)
    
    # replace each url in text string with placeholder
    for url in detected_urls:
        text = text.replace(url, "urlplaceholder")

    # tokenize text
    tokens = word_tokenize(text)
    
    # initiate lemmatizer
    lemmatizer = WordNetLemmatizer()

    # iterate through each token
    clean_tokens = []
    for tok in tokens:
        
        # lemmatize, normalize case, and remove leading/trailing white space
        clean_tok = lemmatizer.lemmatize(tok).lower().strip()
        clean_tokens.append(clean_tok)
        
    return clean_tokens

class StartingVerbExtractor(BaseEstimator, TransformerMixin):
    '''
    Custom class to extract the starting verb of a sentence
    '''

    def starting_verb(self, text):
        sentence_list = nltk.sent_tokenize(text)
        for sentence in sentence_list:
            pos_tags = nltk.pos_tag(tokenize(sentence))
            first_word, first_tag = pos_tags[0]
            if first_tag in ['VB', 'VBP'] or first_word == 'RT':
                return True
        return False

    def fit(self, X, Y=None):
        return self

    def transform(self, X):
        X_tagged = pd.Series(X).apply(self.starting_verb)
        return pd.DataFrame(X_tagged)

def build_model():
    '''
    This machine pipeline should take in the message column as input and output classification results on the other 36 categories in the dataset.
    
    
    '''
    model = Pipeline([
        ('features', FeatureUnion([

         ('text_pipeline', Pipeline([
             ('vect', CountVectorizer(tokenizer=tokenize)),
             ('tfidf', TfidfTransformer())
         ])),

          ('starting_verb', StartingVerbExtractor())
        ])),

        ('clf', MultiOutputClassifier(DecisionTreeClassifier()))
    ])
    
    parameters = {'clf__estimator__min_samples_split': [2, 3, 4],
              'clf__estimator__n_estimators': [20, 40, 60]
    }
    
    return model

def evaluate_model(model, X_test, Y_test, category_names):
    '''
    Function shows the accuracy, precision, and recall of the tuned model as a classification report.
    
    Input:
    model - ML model returned from build_model()
    X-test - feature variables
    Y-test - target variables
    category_names - names of message categories
    
    Output:
    classification_report - 
    '''
    
    Y_pred = model.predict(X_test)
   
    print(classification_report(Y_test.values, Y_pred, target_names=category_names))


def save_model(model, model_filepath):
    '''
    Function exports model as a pickle file
    
    Inputs:
    model - ML model from build_model()
    model_filepath - filepath with name to be saved as a .pkl file
    '''
    pickle.dump(model, open(model_filepath, 'wb'))
    
    


def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        df, X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model.fit(X_train, Y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()