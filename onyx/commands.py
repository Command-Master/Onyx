import os
import shutil
import json
import inspect
from .enum import axis, anchor, dimension
from .selector import Selector

class Commands:
    def __init__(self, datapack_path, override=False):
        self.datapack_path = os.path.normpath(datapack_path)
        self.datapack_name = os.path.basename(os.path.normpath(datapack_path))
        self.path_list = {}

        if override:
            shutil.rmtree(datapack_path,ignore_errors=True)
            # Generate file structure  
            if not os.path.exists(datapack_path):
                os.makedirs(datapack_path)
            else:
                os.chdir(datapack_path)

            os.makedirs(os.path.join("data", self.datapack_name, "functions"), exist_ok=True)

            # Generate pack.mcmeta
            with open(os.path.join(datapack_path, "pack.mcmeta"), "w+") as mc_meta_file:
                mc_meta_data = {"pack": {"pack_format": 5, "description": f"{self.datapack_name} | generated by Onyx"}}
                json.dump(mc_meta_data, mc_meta_file, indent=4)

    # Starts relative to /data/namespace/functions
    def call(self, function):
        # Get the function path, split it, and then keep only everything past /data/namespace/functions/
        function_path = self.path_list[function.__name__].split(os.sep)
        function_path = function_path[function_path.index('functions') + 1:]   

        with open(os.path.join(self.working_path, inspect.stack()[1][3] + ".mcfunction"), "a") as function_file:
            function_file.write(f"function {self.datapack_name}:{' '.join(function_path)}/{function.__name__}\n")   

    # Path decorator
    def path(self, path):
        def wrapper(function):
            # Normalize the path so "/" doesn't break
            new_path = os.path.normpath(path)

            # Create the path in case it doesn't exist
            os.makedirs(os.path.join(self.datapack_path, "data", self.datapack_name, "functions", new_path), exist_ok=True)

            # Assigns and registers the path in the list
            self.working_path = os.path.join(self.datapack_path, "data", self.datapack_name, "functions", new_path) 
            self.path_list[function.__name__] = self.working_path

            # Generate the mcfunction
            function()
            
            return function
        return wrapper

    # Loop decorator
    def loop(self, function):
        def wrapper():
            # Make the directory if it doesn't exist
            os.makedirs(os.path.join(self.datapack_path, "data", "minecraft", "tags", "functions"), exist_ok=True)

            # Get the tick.json contents
            try:
                with open(os.path.join(self.datapack_path, "data", "minecraft", "tags", "functions", "tick.json"), "r") as tick_json: 
                    current_data = json.load(tick_json)
            except FileNotFoundError:
                current_data = {"values": []}
                    
            # Update (or create) the file
            with open(os.path.join(self.datapack_path, "data", "minecraft", "tags", "functions", "tick.json"), "w+") as tick_json:
                # Get the function path, split it, and then keep only everything past /data/namespace/functions/
                function_path = self.path_list[function.__name__].split(os.sep)
                function_path = function_path[function_path.index('functions') + 1:]   

                # Add the data to the list and dump it
                current_data["values"].append(f"{self.datapack_name}:{'/'.join(function_path)}/{function.__name__}")
                json.dump(current_data, tick_json, indent=4)

            return function
        return wrapper()

    class execute:
        def __init__(self):
            self.command = "execute "

        def align(self, *args):
            axes = []
            for arg in args:
                if not isinstance(arg, axis):
                    raise ValueError(f"Unknown value: {axis}")
                elif arg.value not in args:
                    axes.append(arg.value)    
            self.command += f"align {''.join(axes)}"
            return self

        def anchored(self, anchor_point):
            if not isinstance(anchor_point, anchor):
                raise ValueError(f"Unknown value for 'anchored': {anchor_point}")
            self.command += f"anchored {anchor_point.value} "
            return self

        # "as" is a reserved keyword used in opening files
        def As(self, entity):
            if not isinstance(entity, Selector):
                raise ValueError("'entity' must be a selector object")
            self.command += f"as {entity.build()} "
            return self

        def at(self, entity):
            if not isinstance(entity, Selector):
                raise ValueError("'entity' must be a selector object")
            self.command += f"at {entity.build()} "
            return self

        def as_at(self, entity):
            if not isinstance(entity, Selector):
                raise ValueError("'entity' must be a selector object")
            self.command += f"as {entity.build()} at {entity.build()} "
            return self

        def facing(self, entity=None, pos=None):
            if entity:
                if pos:
                    raise ValueError("You can't provide both an entity and position")
                if not isinstance(entity, Selector):
                    raise ValueError("'entity' must be a selector object")
                self.command += f"facing entity {entity.build()} "
            elif pos:
                if not type(pos) is tuple or not len(pos) == 3:
                    raise ValueError("'pos' must be a tuple of 3 values")
                self.command += f"facing {' '.join(pos)} "
            return self

        # "in" is a reserved keyword used for checking lists, tuples, etc.
        def In(self, dimension_name):
            if not isinstance(dimension_name, dimension):
                raise ValueError(f"Unknown value for 'dimension': {dimension_name}")
            self.command += f"in minecraft:{dimension_name.value} "
            return self

        def positioned(self, pos):
            if type(pos) is not tuple or len(pos) != 3:
                raise ValueError("'pos' must be a tuple of 3 values")
            self.command += f"positioned {' '.join(pos)} "
            return self

        def rotated(self, entity=None, rot=None):
            if entity:
                if rot:
                    raise ValueError("You can't provide both an entity and rotation values")
                if not isinstance(entity, Selector):
                    raise ValueError("'entity' must be a selector object")
                self.command += f"rotated as {entity.build()} "
            elif rot:
                if type(rot) is not tuple or len(rot) != 2:
                    raise ValueError("'rot' must be a tuple of 2 values")
                self.command += f"rotated {' '.join(rot)} "
            else:
                raise ValueError("You must specify either an entity or rotation values")
            return self


    def send(self, command):
        with open(os.path.join(self.working_path, inspect.stack()[1][3] + ".mcfunction"), "a") as function_file:
            function_file.write(f"{command}\n")

    def say(self, text):
        with open(os.path.join(self.working_path, inspect.stack()[1][3] + ".mcfunction"), "a") as function_file:
            function_file.write(f"say {text}\n")