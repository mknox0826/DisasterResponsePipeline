# Import libraries 

import sys
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

def load_data(messages_filepath, categories_filepath):
    '''
    Load the data from csv files
    
    Inputs:
    messages_filepath - filepath for the messages csv file
    categories_filepath - filepath for the categories csv file
    
    Output:
    df - pandas dataframe
    '''
    # Load both datasets
    messages = pd.read_csv(messages_filepath)
    categories = pd.read_csv(categories_filepath)
    
    # Merge datasets
    df = messages.merge(categories, how='outer', on=['id'])
    
    return df
    

def clean_data(df):
    '''
    Transform and concatenate loaded pandas dataframe
    Clean the df of null and duplicate values
    
    
    Input:
        df - pandas dataframe from load_data()
        
    Output:
        df - pandas dataframe with no missing or duplicate values

    '''
    # Split categories into separate columns
    categories = df.categories.str.split(';', expand=True)
    row = categories.iloc[0]
    category_colnames = row.apply(lambda x:x[:-2])
    categories.columns = category_colnames
    
    # Convert category values to binary
    for column in categories:
        # set each value to be the last character of the string
        categories[column] = categories[column].str[-1]
    
        # convert column from string to numeric
        categories[column] = categories[column].astype(np.int32)
     
    categories.related.replace(2,1,inplace=True)
    
    # Replace category columns
    df= df.drop('categories', axis=1)
    df = pd.concat([df,categories], axis=1)
    
    # Drop duplicates
    df = df.drop_duplicates()
    
    return df
    
def save_data(df, database_filename):
    '''
    Save cleaned df from clean_data() to a sqLite database
    
    Inputs:
    df - pandas dataframe from clean_data()
    database_filepath - the filepath where the database will be stored
    
    Output:
    None
    
    '''
    engine = create_engine('sqlite:///' + database_filename)
    df.to_sql('DisasterCleaned', engine, if_exists='replace', index=False)
                             
    pass 

def main():
    '''
    Executes all the data processing functions
    1 -Extract the csv files
    2- Transform the data through pre-processing and cleaning
    3- Load cleaned dataframe in a sqlite database
    '''
    if len(sys.argv) == 4:

        messages_filepath, categories_filepath, database_filepath = sys.argv[1:]

        print('Loading data...\n    MESSAGES: {}\n    CATEGORIES: {}'
              .format(messages_filepath, categories_filepath))
        df = load_data(messages_filepath, categories_filepath)

        print('Cleaning data...')
        df = clean_data(df)
        
        print('Saving data...\n    DATABASE: {}'.format(database_filepath))
        save_data(df, database_filepath)
        
        print('Cleaned data saved to database!')
    
    else:
        print('Please provide the filepaths of the messages and categories '\
              'datasets as the first and second argument respectively, as '\
              'well as the filepath of the database to save the cleaned data '\
              'to as the third argument. \n\nExample: python process_data.py '\
              'disaster_messages.csv disaster_categories.csv '\
              'DisasterCleaned.db')


if __name__ == '__main__':
    main()