# Lion-Lottery
A simple app to display the lottery numbers for Columbia University's housing lottery information in an organized way.

## Setup Instructions
1. Create a directory named `data`.
2. Download the housing lottery pdf and place it in `data`. 
3. Create the file `__init__.py` with the following content:

    ```python
    HOUSING_PDF = '[File name of housing lottery pdf]'
    ```
    and place it in `data`.
4. Run the command `python housing.py`.
5. If you want a command line display of sorted data for a certain group size, run the command `python script.py -s [size]`.
