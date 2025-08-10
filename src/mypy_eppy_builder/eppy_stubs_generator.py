import os
import re
from pathlib import Path
from string import ascii_letters, digits
from typing import Optional, cast

from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).parent / "templates"


# --- Utility to parse IDD definitions and generate stubs ---
class EppyStubGenerator:
    def __init__(
        self, idd_path: str, output_dir: str, template_dir: str = str(TEMPLATE_DIR), idf_cls: type | None = None
    ):
        """Create generator.

        Parameters
        ----------
        idd_path: str
            Path to IDD file (currently unused, retained for future parsing logic).
        output_dir: str
            Directory where .pyi stubs are written.
        template_dir: str
            Directory containing Jinja2 templates.
        idf_cls: optional type
            Optional custom IDF class (primarily for testing). If omitted the
            archetypal.idfclass.IDF is imported lazily here to avoid binding it
            before tests can monkeypatch a stub implementation.
        """
        self.idd_path = idd_path
        self.output_dir = output_dir
        if idf_cls is None:  # Lazy import to allow test stubbing
            from archetypal.idfclass import IDF as _IDF  # type: ignore[import-not-found]

            idf_cls = _IDF
        self.idf = idf_cls()
        self.env = Environment(  # noqa: S701
            loader=FileSystemLoader(template_dir),
            trim_blocks=False,
            lstrip_blocks=False,
        )

    def normalize_classname(self, obj_name: str) -> str:
        """Return a valid Python class name for an IDD object.

        EnergyPlus object names can contain characters such as spaces or
        colons (e.g. ``BuildingSurface:Detailed``).  The original
        implementation applied :py:meth:`str.title` which lower-cased
        characters following an existing capital, producing names like
        ``Buildingsurface_Detailed``.  That behaviour broke the expected
        camel-casing of many IDD objects.

        This version simply replaces any non alpha-numeric character with an
        underscore while preserving the original casing of the remaining
        characters so the example above becomes
        ``BuildingSurface_Detailed``.
        """

        return re.sub(r"[^0-9a-zA-Z]+", "_", obj_name.strip())

    def normalize_field_name(self, field_name: str) -> str:
        """Normalize field names using same process as `eppy`."""

        def onlylegalchar(name):
            """return only legal chars"""
            legalchar = ascii_letters + digits + " "
            return "".join([s for s in name[:] if s in legalchar])

        def makefieldname(namefromidd):
            """made a field name that can be used by bunch"""
            newname = onlylegalchar(namefromidd)
            bunchname = newname.replace(" ", "_")
            return bunchname

        return makefieldname(field_name)

    def _get_numeric_limits(self, field: dict[str, list[str]]) -> dict[str, str]:
        """Return pydantic Field constraints from an IDD field definition."""
        mapping = {
            "minimum": "ge",
            "minimum>": "gt",
            "maximum": "le",
            "maximum<": "lt",
        }
        limits: dict[str, str] = {}
        for key, arg in mapping.items():
            val = field.get(key, [""])[0]
            if val not in (None, ""):
                limits[arg] = val
        return limits

    def _format_default(self, base_type: str, value: str) -> Optional[str]:
        if value in (None, "", "none", "NONE", "None"):
            return None
        if base_type == "str" or base_type.startswith("Literal"):
            return repr(value)
        return value

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

    def render_class_stub(self, obj: dict, fields: list[dict[str, list[str]]]) -> str:
        classname = self.normalize_classname(obj["idfobj"])

        def _sanitize_doc(text: str) -> str:
            # Escape triple quotes and backslashes to keep docstring valid
            return text.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')

        raw_memo = obj.get("memo", [""])[0]
        class_memo = _sanitize_doc(raw_memo)
        stub_fields = []
        for field in fields:
            field_name = self.normalize_field_name(field["field"][0])
            base_type = self.get_field_type(field)
            limits = self._get_numeric_limits(field) if base_type in {"int", "float"} else {}
            field_args = []
            default_val = self._format_default(base_type, field.get("default", [""])[0])
            field_args.extend(f"{k}={v}" for k, v in limits.items())
            # If 'required-field' is present, always add a default (even if None)
            require_field = "required-field" in field
            if default_val is not None:
                field_args.append(f"default={default_val}")
            elif require_field:
                field_args.insert(0, "default=...")
            field_note = _sanitize_doc(field.get("note", [""])[0])
            stub_fields.append({
                "name": field_name,
                "type": f"Annotated[{base_type}, Field({', '.join(field_args)})]",
                "note": field_note,
            })
        template = self.env.get_template("common/class_stub.pyi.jinja2")
        return cast(
            str,
            template.render(
                classname=classname,
                class_memo=class_memo,
                fields=stub_fields,
            ),
        )

    def generate_stubs(self) -> None:
        os.makedirs(self.output_dir, exist_ok=True)
        idd_info: list[list[dict]] = self.idf.idd_info  # type: ignore[var-annotated]

        for obj, *fields in idd_info[1:]:
            stub_content = self.render_class_stub(obj, fields)
            file_name = f"{self.normalize_classname(obj['idfobj'])}.pyi"
            with open(os.path.join(self.output_dir, file_name), "w") as stub_file:
                stub_file.write(stub_content)
        print(f"Stubs generated successfully in {self.output_dir}")


def classname_to_key(classname: str) -> str:
    """Convert a normalized class name to an EnergyPlus key form.

    Retained for backwards compatibility (used by new CLI).
    """
    parts = [p for p in classname.split("_") if p]
    return ":".join(part.upper() for part in parts)


# --- Main usage example ---
if __name__ == "__main__":
    # Provide your IDD file path and desired output directory for stubs
    idd_file = "/Applications/EnergyPlus-23-1-0/Energy+.idd"
    stubs_output_dir = "./typings/eppy"

    generator = EppyStubGenerator(idd_file, stubs_output_dir)
    generator.generate_stubs()
    # Legacy manual invocation retained for reference; new workflow uses cli.py
