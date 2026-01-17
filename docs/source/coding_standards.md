(coding-standards)=
# Coding Standards
## File name guidelines
* Files in qt_node_editor package start with `node_`
* files containing graphical representation (PyQt6 overriden classes) start with ```node_graphics_```
* files for window/widget start with ```node_editor_```

## Coding guidelines

* overriden Qt methods use Camel case naming
* other methods, variables/properties use Snake case naming

* constructor ```__init__``` always contains all class variables for entire class. This is helpful for new users 
  to just look at the constructor and read about all properties that class is using. Nobody wants any 
  surprises hidden in the code later
* nodeeditor uses custom callbacks and listeners. Methods for adding callback functions
  are usually named ```add_xy_listener```
* custom events are usually named ```on_xy```
* methods named ```do_xy``` usually *do* certain task and also take care off low level operations
* classes always contain methods in this order:
    * ```__init__```
    * Python magic methods (i.e. `__str__`), getters and setters
    * ```init_xy``` functions
    * listener functions
    * nodeeditor event fuctions
    * nodeeditor ```do_xy``` and ```get_xy``` helping functions 
    * Qt6 event functions
    * other functions
    * optionally overriden Qt ```paint``` method
    * ```serialize``` and ```deserialize``` methods at the end    
