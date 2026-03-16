'''
File name: mappings.py
Purpose: This script holds mappings of raw data and files to match file names and user
Created by: Alton Hipps
Last Modified: 03/15/2026
'''

ID_to_GPX={ # This piece is still manual and could be tough with more files. These are placeholder names
    'R_surveyID1':('dog_fitFile1_w_no_extension','human_fitFile1_w_no_extension'),
    'R_surveyID2':('dog_fitFile2_w_no_extension','human_fitFile2_w_no_extension')
}

dogOrHuman={ # keep track of who is what
    'Dog':('dog_fitFile1_w_no_extension',
           'dog_fitFile2_w_no_extension'),
    'Human':('human_fitFile1_w_no_extension',
             'human_fitFile2_w_no_extension')
}
