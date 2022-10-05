# Documentation reorganization plan

### Goals for Programmer documentation

1. **completeness** Documentation reflects code: each .py and each class is referenced and explained in the documentation. 
2. **Readability** All terms need to be explained before they are used, examples: django, controller, URL ...
3. **limited scope** Each document file should explain a limited, well define subject. Different subjects should be described in different files.
4. **information hiding** There is a consistent hierarchy in the documentation where each level hides non-critical aspects of the code below it, exposes minimal set of parameters that are used at higher levels. 
5. Automatic generation, using tools such as Sphinx the documentation is combined with the code. A compiler can then be used that translates the documentation into a easy to navvigate web format.

## Issues with current programmer documentation.

1. **Incompleteness:** The file lsr-code.txt lists all of the files in the pipeliine directory, there are about 1000 files in this directory. I found no reference to any individual files in the programmer documentation.
2. **confusing terminology** Are we calling *all* of the code the "pipeline", or is the piepline specific to what is sometime called the "czi.2.neuroglancer" code? I think that structure detection, marked cell detection and alignment should be in separate directories.
3. **Strong dependenciess between the code and the database** This issue is a documentation issue and a design issue: a lot of the code is written specifically to work with the database and with django. This makes it harder to understand the code and to isolate bugs.  The django code should have a common and simple API so that the rest of the code does not have to be changed if we choose to switch from django to something else or if we want to give a part of the code (for example the marked cell detector) to anther lab.
4. The file ` programmer/high.level.overall.design.of.projects.md `  is incoherent and too long. I wrote what I believe is a better version in 







### Goals for user Documentation

1. **Task Specific** a typical user wants to use the system in a particular way. It is therefor desirable to create a specialized documentation for each workflow. Parts of the workflows can be common, so they can be put in files that are poointed to by the workflow documentation.
2. **Completeness:** The documentation should note assume prior knowledge of the user. The explanation should be step-by-step.
3. **Readability** The explanation should be written in good english and explain all terms before they are used.