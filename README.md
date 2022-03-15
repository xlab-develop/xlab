![xLab Logo](https://github.com/csalcedo001/xlab/blob/main/docs/img/xlab_logo.png)

-------------------------------------------------------------------

xLab is an experiment execution tool that automates tasks in research-oriented projects. It provides a simple interface that can be integrated to project executables with minimum modifications. xLab enables the following functionalities:

- Maintaining a folder structure for runs.
- Caching results saved after each run.
- Accessing cached results from a Python dictionary of arguments.

# Installation

```
pip install xlab
```

# Quickstart

1. Run `xlab project init` on the root directory of your project.
2. Wrap the code of your executables within a _with_ clause such that it resembles the following pattern:

```python
# Import libraries...

import xlab.experiment as exp

# ...

parser = get_parser()

with exp.setup(parser) as setup:
    args = setup.args
    dir = setup.dir

    # Use args to run experiment and
    # dir as a directory to save results

# ...
```

3. Call your program either directly from the terminal or indirectly through another script.

If you executable could be run on the terminal before using xLab, now you can continue running the program in the same way as before, but now with results cached and automatically saved in a folder structure. 

You can also run the executable within a Python script by using the following code structure:

```python
# Import libraries...

import xlab.experiment as exp

# ...

e = exp.Experiment(executable, required_args, command)

print(e.args) # Prints all arguments (both required and optional)

# Modify e.args as you wish...

e.run()
```
