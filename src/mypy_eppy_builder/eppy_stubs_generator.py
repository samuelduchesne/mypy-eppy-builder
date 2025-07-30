import os
import re
from pathlib import Path

from archetypal import IDF


# --- Utility to parse IDD definitions and generate stubs ---
class EppyStubGenerator:
    def __init__(self, idd_path: str, output_dir: str):
        self.idd_path = idd_path
        self.output_dir = output_dir
        self.idf = IDF()

    def normalize_classname(self, obj_name: str) -> str:
        return re.sub(r"[^a-zA-Z0-9]", "_", obj_name.title())

    def get_field_type(self, field: dict[str, list[str]]) -> str:
        field_type = field.get("type", ["alpha"])[0]
        if field_type == "real":
            return "float"
        elif field_type == "integer":
            return "int"
        elif field_type == "choice":
            choices = field.get("key", [])
            if choices:
                return f"Literal[{', '.join(map(repr, choices))}]"
            else:
                return "str"
        else:
            return "str"

    def generate_stub_content(self, obj: dict, fields: list[dict[str, list[str]]]) -> str:
        classname = self.normalize_classname(obj["idfobj"])
        class_memo = obj.get("memo", [""])[0]
        lines = [f"class {classname}(EpBunch):"]
        if class_memo:
            # Ensure the memo ends with a punctuation mark.
            memo = class_memo.rstrip()
            if memo and memo[-1] not in ".!?":
                memo += "."
            lines.append(f'    """{memo}"""\n')
        if not fields:
            lines.append("    pass")
            return "\n".join(lines)

        for field in fields:
            field_name = self.normalize_classname(field["field"][0])
            field_type = self.get_field_type(field)
            field_note = field.get("note", [""])[0]
            field_default = field.get("default", [""])[0]
            if field_default:
                if field_type == "str":
                    lines.append(f'    {field_name}: {field_type} = "{field_default}"')
                else:
                    lines.append(f"    {field_name}: {field_type} = {field_default}")
            else:
                lines.append(f"    {field_name}: {field_type}")
            if field_note:
                lines.append(f'    """{field_note}"""')

        return "\n".join(lines)

    def generate_stubs(self):
        os.makedirs(self.output_dir, exist_ok=True)
        idd_info: list[list[dict]] = self.idf.idd_info

        for obj, *fields in idd_info[1:]:
            stub_content = self.generate_stub_content(obj, fields)
            file_name = f"{self.normalize_classname(obj['idfobj'])}.pyi"

            with open(os.path.join(self.output_dir, file_name), "w") as stub_file:
                stub_file.write("from typing import Literal\n\n")
                stub_file.write("from geomeppy.patches import EpBunch\n\n")
                stub_file.write(stub_content)

        print(f"Stubs generated successfully in {self.output_dir}")


HEADER = """from typing import overload, Literal

from geomeppy.patches import EpBunch

"""

FOOTER = """
class IDF:
"""


def classname_to_key(classname: str) -> str:
    parts = classname.split("_")
    return ":".join(part.upper() for part in parts)


def generate_overloads(stubs_dir: str, output_file: str):
    imports = []
    overloads = []

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    for file in os.listdir(stubs_dir):
        if file.endswith(".pyi"):
            classname = file[:-4]  # remove .pyi extension
            module_import = f"from eppy.{classname} import {classname}"
            imports.append(module_import)

            ep_key = classname_to_key(classname)
            overload = f'''
    @overload
    def newidfobject(self, key: Literal["{ep_key}"], **kwargs) -> {classname}: ...

    @overload
    def idfobjects(self, key: Literal["{ep_key}"]) -> list[{classname}]: ...
'''
            overloads.append(overload)

    with open(output_file, "w") as f:
        f.write(HEADER)
        f.write("\n".join(imports))
        f.write(FOOTER)
        f.write("".join(overloads))

        # default definitions
        f.write("""
    def newidfobject(self, key: str, **kwargs) -> EpBunch: ...
    def idfobjects(self, key: str) -> list[EpBunch]: ...
""")


# --- Main usage example ---
if __name__ == "__main__":
    # Provide your IDD file path and desired output directory for stubs
    idd_file = "/Applications/EnergyPlus-23-1-0/Energy+.idd"
    stubs_output_dir = "./typings/eppy"

    generator = EppyStubGenerator(idd_file, stubs_output_dir)
    generator.generate_stubs()
    generate_overloads(stubs_output_dir, "./typings/archetypal/idfclass/idf.pyi")
