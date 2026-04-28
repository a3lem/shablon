"""Tests for .shablon/vars.<ext> discovery and execution.

# spec: variables requirement=optional-variables-file
# spec: variables requirement=single-variables-file
# spec: variables requirement=variables-file-must-be-executable
# spec: variables requirement=subprocess-contract
# spec: variables requirement=stdout-must-be-a-json-object
# spec: variables requirement=top-level-keys-become-render-variables
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest

from shablon.errors import ShablonError
from shablon.variables import resolve
from tests.helpers import vars_script


def _shabdir(project: Path) -> Path:
    return project / ".shablon"


# spec: variables requirement=optional-variables-file scenario=no-vars-file
def test_no_vars_file_returns_empty(project: Path) -> None:
    assert resolve(_shabdir(project)) == {}


# spec: variables requirement=optional-variables-file scenario=vars-py-present
# spec: variables requirement=top-level-keys-become-render-variables scenario=nested-values-preserved
def test_happy_path_python(project: Path) -> None:
    vars_script(
        _shabdir(project),
        "py",
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import json
            print(json.dumps({"version": "1.0", "project": {"name": "foo"}}))
            """
        ),
    )
    ctx = resolve(_shabdir(project))
    assert ctx == {"version": "1.0", "project": {"name": "foo"}}


# spec: variables requirement=single-variables-file scenario=two-vars-files
def test_multiple_vars_files_rejected(project: Path) -> None:
    vars_script(_shabdir(project), "py", '#!/bin/sh\necho "{}"\n')
    vars_script(_shabdir(project), "sh", '#!/bin/sh\necho "{}"\n')
    with pytest.raises(ShablonError, match="vars.py.*vars.sh|vars.sh.*vars.py"):
        resolve(_shabdir(project))


# spec: variables requirement=variables-file-must-be-executable scenario=non-executable-vars-py
def test_non_executable_rejected(project: Path) -> None:
    path = _shabdir(project) / "vars.py"
    path.write_text("#!/usr/bin/env python3\nprint('{}')\n", encoding="utf-8")
    path.chmod(0o644)
    with pytest.raises(ShablonError, match="not executable"):
        resolve(_shabdir(project))


# spec: variables requirement=subprocess-contract scenario=non-zero-exit
def test_non_zero_exit_rejected(project: Path) -> None:
    vars_script(
        _shabdir(project),
        "sh",
        "#!/bin/sh\necho boom 1>&2\nexit 2\n",
    )
    with pytest.raises(ShablonError, match="status 2"):
        resolve(_shabdir(project))


# spec: variables requirement=subprocess-contract scenario=project-root-visible-to-script
def test_subprocess_contract(project: Path) -> None:
    vars_script(
        _shabdir(project),
        "sh",
        textwrap.dedent(
            """\
            #!/bin/sh
            cat <<EOF
            {
              "cwd": "$(pwd)",
              "root": "$SHABLON_PROJECT_ROOT",
              "argc": $#,
              "stdin_eof": $(if [ -t 0 ] || ! read -r line 2>/dev/null; then echo true; else echo false; fi)
            }
            EOF
            """
        ),
    )
    ctx = resolve(_shabdir(project))
    assert ctx["cwd"] == str(project.resolve())
    assert ctx["root"] == str(project.resolve())
    assert ctx["argc"] == 0
    assert ctx["stdin_eof"] is True


# spec: variables requirement=stdout-must-be-a-json-object scenario=non-object-json
def test_non_object_json_rejected(project: Path) -> None:
    vars_script(_shabdir(project), "sh", "#!/bin/sh\necho '[1, 2, 3]'\n")
    with pytest.raises(ShablonError, match="JSON object"):
        resolve(_shabdir(project))


# spec: variables requirement=stdout-must-be-a-json-object scenario=invalid-json
def test_invalid_json_rejected(project: Path) -> None:
    vars_script(_shabdir(project), "sh", "#!/bin/sh\necho 'not json'\n")
    with pytest.raises(ShablonError, match="invalid JSON"):
        resolve(_shabdir(project))


def test_extra_extensions_dont_match(project: Path) -> None:
    """vars.py.bak should not match vars.<ext>."""
    bad = _shabdir(project) / "vars.py.bak"
    bad.write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
    bad.chmod(0o755)
    assert resolve(_shabdir(project)) == {}
