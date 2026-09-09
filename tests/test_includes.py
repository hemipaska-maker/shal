"""`include:` — compose a setup from many topology files (shal#134).

Design (CTO ruling, 2026-09-04, option B): `include:` is a top-level list of
relative paths. Each included file is a full topology with its own `root:`;
those `root:` maps merge as SIBLINGS into the main file's `root:` — nothing
nests. No override: a duplicate top-level name across any two files is a
`LoadError` naming both files, so include order never matters. Confinement and
the cycle guard reuse the same machinery as `use:`. Only the main file's
`.env` is read.
"""
import textwrap
from pathlib import Path

import pytest

import shal

DEVICE = """\
shal_version: 1
root:
  {name}:
    driver: shal,sim-i2c
    address: {bus}
    children:
      temp0:
        id: {name}_temp
        driver: ti,tmp102
        address: 0x48
"""


def write(p: Path, body: str) -> Path:
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return p


def test_two_files_one_device_each_load_as_one_setup(tmp_path):
    write(tmp_path / "device_a.yaml", DEVICE.format(name="device_a", bus="sim0"))
    write(tmp_path / "device_b.yaml", DEVICE.format(name="device_b", bus="sim1"))
    main = write(tmp_path / "main.yaml", """
        shal_version: 1
        include:
          - device_a.yaml
          - device_b.yaml
    """)
    with shal.load(main) as hal:
        a = hal.get_device("device_a_temp")
        b = hal.get_device("device_b_temp")
        assert a is not b
        assert a.read_celsius() == pytest.approx(25.0, abs=0.07)
        assert hal.get_node("device_a_temp").path == "/device_a/temp0"
        assert hal.get_node("device_b_temp").path == "/device_b/temp0"
        # both devices show up on the agent tool surface ("shal tools")
        names = {s["name"] for s in hal.tool_schemas()}
        assert any("device_a" in n for n in names)
        assert any("device_b" in n for n in names)


def test_main_file_can_mix_own_root_with_includes(tmp_path):
    write(tmp_path / "device_b.yaml", DEVICE.format(name="device_b", bus="sim1"))
    main = write(tmp_path / "main.yaml", """
        shal_version: 1
        root:
          device_a:
            driver: shal,sim-i2c
            address: sim0
            children:
              temp0: { id: device_a_temp, driver: "ti,tmp102", address: 0x48 }
        include:
          - device_b.yaml
    """)
    with shal.load(main) as hal:
        assert hal.get_device("device_a_temp") is not None
        assert hal.get_device("device_b_temp") is not None


def test_duplicate_root_name_across_files_names_both_files(tmp_path):
    write(tmp_path / "device_a.yaml", DEVICE.format(name="dup", bus="sim0"))
    write(tmp_path / "device_b.yaml", DEVICE.format(name="dup", bus="sim1"))
    main = write(tmp_path / "main.yaml", """
        shal_version: 1
        include:
          - device_a.yaml
          - device_b.yaml
    """)
    with pytest.raises(shal.LoadError) as exc:
        shal.load(main)
    msg = str(exc.value)
    assert "duplicate top-level name" in msg
    assert "device_a.yaml" in msg
    assert "device_b.yaml" in msg


def test_include_order_is_irrelevant_to_the_duplicate_error(tmp_path):
    # no override means the same pair of files errors regardless of order
    write(tmp_path / "device_a.yaml", DEVICE.format(name="dup", bus="sim0"))
    write(tmp_path / "device_b.yaml", DEVICE.format(name="dup", bus="sim1"))
    main = write(tmp_path / "main.yaml", """
        shal_version: 1
        include:
          - device_b.yaml
          - device_a.yaml
    """)
    with pytest.raises(shal.LoadError, match="duplicate top-level name"):
        shal.load(main)


def test_escape_above_root_is_rejected(tmp_path):
    (tmp_path / "project").mkdir()
    write(tmp_path / "outside.yaml", DEVICE.format(name="outside", bus="sim0"))
    main = write(tmp_path / "project" / "main.yaml", """
        shal_version: 1
        include:
          - ../outside.yaml
    """)
    with pytest.raises(shal.LoadError, match="escapes the topology root"):
        shal.load(main)


def test_cycle_is_caught_and_names_the_chain(tmp_path):
    write(tmp_path / "a.yaml", """
        shal_version: 1
        include:
          - b.yaml
    """)
    write(tmp_path / "b.yaml", """
        shal_version: 1
        include:
          - a.yaml
    """)
    with pytest.raises(shal.LoadError, match="circular include") as exc:
        shal.load(tmp_path / "a.yaml")
    msg = str(exc.value)
    assert "a.yaml" in msg
    assert "b.yaml" in msg


def test_include_chain(tmp_path):
    # main -> a.yaml -> b.yaml (b has the actual device)
    write(tmp_path / "b.yaml", DEVICE.format(name="leaf", bus="sim0"))
    write(tmp_path / "a.yaml", """
        shal_version: 1
        include:
          - b.yaml
    """)
    main = write(tmp_path / "main.yaml", """
        shal_version: 1
        include:
          - a.yaml
    """)
    with shal.load(main) as hal:
        assert hal.get_device("leaf_temp") is not None


def test_missing_include_file(tmp_path):
    main = write(tmp_path / "main.yaml", """
        shal_version: 1
        include:
          - nope.yaml
    """)
    with pytest.raises(shal.LoadError, match="not found"):
        shal.load(main)


def test_include_may_not_take_with(tmp_path):
    write(tmp_path / "device_a.yaml", DEVICE.format(name="device_a", bus="sim0"))
    main = write(tmp_path / "main.yaml", """
        shal_version: 1
        include:
          - path: device_a.yaml
            with: { x: 1 }
    """)
    with pytest.raises(shal.LoadError, match="schema violation"):
        shal.load(main)


def test_schema_validated_per_included_file_names_that_file(tmp_path):
    write(tmp_path / "bad.yaml", """
        shal_version: 1
        root:
          a: { driver: "shal,sim-i2c", address: sim0, not_a_real_key: 1 }
    """)
    main = write(tmp_path / "main.yaml", """
        shal_version: 1
        include:
          - bad.yaml
    """)
    with pytest.raises(shal.LoadError) as exc:
        shal.load(main)
    msg = str(exc.value)
    assert "schema violation" in msg
    assert "bad.yaml" in msg


def test_main_file_may_be_include_only(tmp_path):
    write(tmp_path / "device_a.yaml", DEVICE.format(name="device_a", bus="sim0"))
    main = write(tmp_path / "main.yaml", """
        shal_version: 1
        include:
          - device_a.yaml
    """)
    with shal.load(main) as hal:
        assert hal.get_device("device_a_temp") is not None


def test_including_a_template_file_is_an_error(tmp_path):
    # board.yaml is a `use:` template (template:, no root:) — including it
    # would otherwise "load" successfully while contributing nothing (#137).
    write(tmp_path / "board.yaml", """
        shal_version: 1
        template:
          driver: "shal,sim-i2c"
          address: "sim0"
          children:
            t: { id: t0, driver: "ti,tmp102", address: 0x48 }
    """)
    main = write(tmp_path / "main.yaml", """
        shal_version: 1
        include:
          - board.yaml
    """)
    with pytest.raises(shal.LoadError, match="cannot be include"):
        shal.load(main)


def test_dotenv_beside_included_file_is_not_read(tmp_path, monkeypatch):
    monkeypatch.delenv("SHAL_TEST_INCLUDE_SECRET", raising=False)
    sub = tmp_path / "sub"
    sub.mkdir()
    write(sub / ".env", "SHAL_TEST_INCLUDE_SECRET=leaked\n")
    write(sub / "device_a.yaml", """
        shal_version: 1
        root:
          device_a:
            driver: shal,sim-i2c
            address: "${SHAL_TEST_INCLUDE_SECRET}"
            children:
              temp0: { id: device_a_temp, driver: "ti,tmp102", address: 0x48 }
    """)
    main = write(tmp_path / "main.yaml", """
        shal_version: 1
        include:
          - sub/device_a.yaml
    """)
    # the included file's own address needs the var but its sibling .env is
    # never read — only the main file's .env would be — so this fails exactly
    # like a genuinely unset environment variable.
    with pytest.raises(shal.LoadError, match="not set"):
        shal.load(main)
