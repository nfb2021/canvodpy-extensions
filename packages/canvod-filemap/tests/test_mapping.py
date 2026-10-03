"""Tests for canvod.filemap.mapping."""

from canvod.filemap.mapping import VirtualFile
from canvod.preflight.convention import CanVODFilename, ReceiverType


class TestVirtualFile:
    def test_canonical_str(self, tmp_path):
        p = tmp_path / "test.rnx"
        p.write_bytes(b"data")

        cn = CanVODFilename(
            site="ROS",
            receiver_type=ReceiverType.REFERENCE,
            receiver_number=1,
            agency="TUW",
            year=2025,
            doy=1,
        )
        vf = VirtualFile(physical_path=p, conventional_name=cn)
        assert vf.canonical_str == "ROSR01TUW_R_20250010000_01D_05S_AA.rnx"

    def test_open(self, tmp_path):
        p = tmp_path / "test.rnx"
        p.write_bytes(b"hello")

        cn = CanVODFilename(
            site="ROS",
            receiver_type=ReceiverType.REFERENCE,
            receiver_number=1,
            agency="TUW",
            year=2025,
            doy=1,
        )
        vf = VirtualFile(physical_path=p, conventional_name=cn)
        with vf.open() as f:
            assert f.read() == b"hello"
