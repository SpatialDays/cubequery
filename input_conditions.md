# Input Conditions

In relation to the **input_conditions.json** file found in the */cubequery/* directory. This file assists with the validation on both the front-end and the backend. It also provides support for additional dynamic functions.

## Explanation
The first key dictates the ID that is required to change in order for the conditions to be rendered. In this example, when **platform** is changed and **SENTINTEL_2** is picked, there are three conditions that must be met. The three types are *int_range*, *add* and *date_range*. The front-end and backend code will run the function associated with these types and ensure that the values are expected. Please see the explanation of types to understand what the values means.

## Types
### Int_Range
Establishes an integer boundary for the IDs specified.
* The value must be provided in a list array format and each of integer type.
* If the array consists of 2 or more values then the boundary will be set between the minimum and maximum of the array of integers. 
* If only one integer value in array then it will be assumed to be minimum only and a max will not be set.

### Date_Range
Establishes a date boundary for the IDs specified
* The value must be provided in a list array format and each of string YYYY-MM-DD format.
* If the array consists of 2 or more values then the boundary will be set between the minimum and maximum of the array of dates. 
* If only one date value in array then it will be assumed to be minimum only and a max will not be set.

### Add
Appends an additional value to the IDs specified.
* Only works with select and similar DOM types.
* Value must be an array format with either string or integer type.

### Display_Text
Changes label value on select option
* Does not change the actual value sent and received from server, only what is visible to the user
* It is possible to only change a single label out of multiple values

## Error Messages
When validating the arguments passed in from the back-end, all unexpected values will be passed into an error array to be presented in the front-end. This will contain the error_message value from the JSON file. Not to be confused with _comment which is in reference only for the developer to get an explanation as to what the validation is checking for.

## Processes
If an array of processes are given, the conditions will only apply to those processes listed. 
* If no processes are given, then all of them are applied

## Example

The JSON file is structured in such a way that it is readable by the Python backend and the Javascript validation on the front-end. 

```json
{
  "platform": [ <!-- ID of the input that conditionally impacts another -->
    {
      "name": "SENTINEL_2", <!-- If that ID has value of -->
      "conditions": [ <!-- Inspect conditions -->
        {
          "id": [ <!-- List of ID's that are affected by change of initial ID's value -->
            "res"
          ],
          "value": [ <!-- Values to set (dependent on type) -->
            10,
            30
          ],
          "type": "int_range", <!-- Type  -->
          "_comment": "Satellite capable of set resolution range", <!-- Comment only visible for developer -->
          "error_message": "The resolution specified does not match the satellites capabilities" <!-- Error message visible to client -->
        },
        {
          "id": [
            "indices"
          ],
          "value": [
            "CHLORPHYLL"
          ],
          "type": "add", <!-- Type -->
          "_comment": "Satellite contains extra indice data.",
          "processes": [ <!-- Specific to this process -->
                "processes.aggregate_indices.AggregateIndices"
            ]
        },
        {
          "id": [
            "start_date",
            "end_date"
          ],
          "value": [
            "2003-01-01",
            "2005-01-01"
          ],
          "type": "date_range", <!-- Type -->
          "_comment": "Satellite only active between these two dates. If only one date provided, it means the satellite is still active.",
          "error_message": "Dates not matching with satellite capabilities"
        }
      ]
    }
  ]
}
```

