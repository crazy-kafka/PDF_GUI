For the data in timing report, they are classified by multiple path groups.
For example, there are two groups: REG2REG, IO. Now the table header is one column style and timing information part in table has to defined as
```
step   | REG2REG_wns | REG2REG_tns | REG2REG_nvp | IO_wns | IO_tns | IO_nvp |
—————————————————————————————————————————————————————————————————————————————— 
step_a | 0.1         | 10.0        | 100         | 0.1    | 10.0   | 100    | 
```
It will cause table to be too long. Now it is required to create new config interface to create more compact layout, which should be like below:
```
step   |     REG2REG     |       IO        | density|
       | wns | tns | nvp | wns | tns | nvp |        |
——————————————————————————————————————————————————————
step_a | 0.1 | 10.0| 100 | 0.1 | 10.0| 100 | 56%    |
```
The timing metrics "wns tns nvp" are grouped by REG2REG after special configuration and IO while other metrics are not affected.

Configuration interface change:
```
metrics:
- key: density
    label: "Density"
    format: ".2f"        
- key: REG2REG@wns
    label: "wns"
    format: ".3f"
- key: REG2REG@tns
    label: "tns"
    format: ".3f"
- key: REG2REG@nvp
    label: "nvp"
    format: ".0f"
- key: IO@wns
    label: "wns"
- key: IO@tns
    label: "tns"
- key: IO@nvp
    label: "nvp"
```
"@" will be special character for mertics name define which is called groyped metric keyword, for example: REG2REG@wns, REG2REG@tns, REG2REG@nvp will be grouped together after parsing, and layout should be changed according to it. If there is not "@" style metric defined, table layout keeps same as before.
The sort and chart should display full name of grouped metric keyword.

Understand this feature and Give your coding plan about layout change, new interface, testing and documentation.
Make less change as much as possible except gui part of code
