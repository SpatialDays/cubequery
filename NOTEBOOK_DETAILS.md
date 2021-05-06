# Note Book Specifications

To use a jupyter notebook with the cube query system there are some things that will need changing.

The title element of the first markdown block will be taken as the display name for the process. The rest of 
that block will be used as the description, after that all markdown blocks will be ignored.

Any code block that starts with `#jupyteronly` will be ignored in the final output. This is so you can put
checks in your notebook and display graphs that won't get output in the final products but are useful for 
checking that the process is working as expected.

Any parameters to your script should be kept in one block. This block should start with the comment `#parameters`
This will take the form of a list of variables e.g:

```python
# parameters

#set baseline start and end of period
#parameter display_name="baseline start date" description="start of the baseline window" datatype="date"
baseline_start_date = '2019-2-1'
#parameter display_name="baseline end date" description="end of the baseline window" datatype="date"
baseline_end_date = '2019-12-30'

#parameter display_name="resolution" description="size of pixes" datatype="int"
res = (30)

#parameter display_name="satellite" description="Satellite to use." datatype="string" options=["SENTINEL_2", "LANDSAT_4", "LANDSAT_5", "LANDSAT_7", "LANDSAT_8"],
platform = "LANDSAT_8"

```

Each variable should have a comment starting with `#parameter` on the line above it. This needs to have the
following three fields `display_name`, `description`, and `datatype` Optionally you can also include the `options` 
which should be a list of valid options.

The last line of the last code block in your script should be a list of the path to the output files.

Things to make sure:
* You've imported the right things in blocks not marked `#jupyteronly`
* the code produces the correct output if you don't run any of the `#jupyteronly` blocks.
