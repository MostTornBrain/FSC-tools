# ----------------------------------------------------------------------
# Definitions of Campaign Cartographer 3+ Symbol-related C structures 
# using Python ctypes.
#
# This module defines structures necessary for creating the symbol entities
# used in CC3+ Symbol Catalog files (.FSC).
#
# These definitions are based on the FastCAD v6 SDK and CC3+ file format
# documentation and .H and .CPY files.
#
# There are two main symbol classes defined here:
# 1) SimpleSymbol: A standard symbol with a single image.
# 2) VaricolorSymbol: A symbol that uses two images for varicolor effects.
#
# Each of these classes encapsulates the required structures in the correct order:
# - SYMDEF: Symbol definition structure.
# - Marker0: Start marker structure.
# - PICTR: Picture entity structure.
# - SYMINFO: Symbol information structure.
# - Marker1: End marker structure.
# 
# The structures are packed to match the C structure layout exactly.
# This module also includes helper functions for working with PNG images
# to retrieve their dimensions, which are needed for symbol definitions.
# ----------------------------------------------------------------------
# Usage:
# Import this module and create instances of SimpleSymbol or VaricolorSymbol
# by providing the necessary parameters such as symbol name and image file paths.
#
# Example:
#  from FSCtypes import SimpleSymbol, VaricolorSymbol
#  
#  simple_sym = SimpleSymbol("MySymbol", "path/to/image.png", isGroup=False)
#  vari_sym = VaricolorSymbol("MyVaricolorSymbol", "path/to/image1.png", "path/to/image2.png", isGroup=True)
#
# These instances can then be converted to bytes and written to FSC files
# assuming you create the appropriate file structure around them.
# See the `FSC_create_Symbol_catalog.py` script for an example of how to use these classes
# to create a complete FSC file.
# ----------------------------------------------------------------------
# Author: Brian Stormont
# Date: 2025-12-06
# Version: 0.1
# License: MIT License
# ----------------------------------------------------------------------

import ctypes
from enum import IntEnum
import os
import struct
import sys

# --- Constants (from .H headers) --------------------------------------------
ET_XP = 4
ET_SYMDEF = 28

RESINFO_COUNT = 4

XPID_PICTR = 0xA004
XT_PICTR = 1

XPID_SYMINFO = 0xA00B
XT_SYMINFO = 97 

# Confirmed sizes from XT_Entities.h static_assert:
# sizeof(CSTUFF) == 28
# sizeof(PICTR)  == 511
# sizeof(SYMINFO == 406)

# Flags for PICTR entity
PF_NO_OUTLINE  =      1
PF_DRAW_IN_XOR =      2
PF_RESINFO_VALID =    4
PF_RESINFO_ONLY1 =    8
PF_USE_CUR_COLOR =   16
PF_ROOF_SHADE    =   32
PF_MIRROR        =   64
PF_SHEAR         =  128

PICTR_VERSION = 0

SYMINFO_VERSION = 1

# Flags for SYMINFO entity
SF_PERSPECTIVES      = 0x00000001  # Shear symbols with control points to perspective view
SF_GROUPED           = 0x00000002  # Symbol is included in a symbol-group
SF_VARICOLOR         = 0x00000004  # Symbol is varicolor. Will change color according to layer.
SF_TRANSFORM         = 0x00000008  # Random transformations
SF_ALONG             = 0x00000010  # Place symbols along entities
SF_EXPLODE           = 0x00000020  # Explode symbols on placement
SF_HEX               = 0x00000040  # Symbol is hex (vertical or horizontal)
SF_HEX_VER           = 0x00000080  # Symbol is vertical hex
SF_FRONTONLAYER      = 0x00000100  # Place symbol in front on current layer
SF_SHEET             = 0x00000200  # Place on sheet
SF_CTRLP_LAYER       = 0x00000400  # CTRLP will only cut on the same layer as the CTRLP
SF_LAYER_TO_SHEET    = 0x00000800  # Split the symbol definition into several sheets
SF_DONT_ADD          = 0x00001000  # Don't add the symbol (for use in "scissors" symbol
SF_VARICOLOR_SHADING = 0x00002000  # Set all shadings as varicolor
SF_STARMAP           = 0x00004000  # Symbol is a starmap symbol
SF_DRAWTOOL          = 0x00008000  # Symbol is a drawing tool
SF_XCHECK_PICTR      = 0x00010000  # Use special XCheck of non-transparent parts of the PICTR entity

# Flags for SYMINFO.GFlags
SGF_NUMBERS          = 0x00000000  # Symbols within group differs by a number
SGF_LETTER           = 0x00000001  # Symbols within group differs by one letter
SGF_SAME_PREFIX      = 0x00000002  # Symbols within group differs by text after the last comma
SGF_VARICOLOR        = 0x00000080  # Only used in call to IsSameSymbolGroup - can be changed
SGF_RANDOM           = 0x00000100  # Select random symbol
SGF_ARROWSYMS        = 0x00000200  # Arrows change symbol Left/Up/Right/Down
SGF_IGNOREINITIALS   = 0x00000400  # Ignores initials at the end of the name

# Flags for SYMINFO.TFlags
TF_OFFSET            = 0x00000001  # random offset fields are valid
TF_ROTATE            = 0x00000002  # random rotate fields are valid
TF_SCALE             = 0x00000004  # random scale fields are valid
TF_SCALE_XY          = 0x00000008  # independent X and Y random scale fields are valid
TF_SHEAR             = 0x00000010  # random rotate fields are valid
TF_MIRROR_X          = 0x00000020  # randomly mirror in X
TF_MIRROR_Y          = 0x00000040  # randomly mirror in Y

#--- Helpers ----------------------------------------------------------

def png_dimensions(file_path):
    """
    Reads the dimensions from a PNG file header using only standard Python libraries.
    """
    try:
        with open(file_path, 'rb') as f:
            data = f.read(24) # Read just the first 24 bytes

        # Check the PNG magic number and the IHDR chunk signature
        if data.startswith(b'\x89PNG\r\n\x1a\n') and data[12:16] == b'IHDR':
            # Unpack the 4-byte width and 4-byte height from bytes 16 to 24
            # '>LL' means Big-Endian (>) Unsigned Long Long (LL, 4 bytes each)
            width, height = struct.unpack(b'>LL', data[16:24])
            return width, height
        else:
            raise ValueError("File is not a valid PNG file or has a corrupted header.")

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}", file=sys.stderr)
        return None, None
    except ValueError as e:
        print(f"Error reading dimensions for {os.path.basename(file_path)}: {e}", file=sys.stderr)
        return None, None


#--- Class Definitions ------------------------------------------------

class IMGXFRMODE(IntEnum):
    IMGX_COPY     = 0
    IMGX_TCOLOR   = 1
    IMGX_ALPHA    = 2
    IMGX_PREALPHA = 3
    IMGX_ULTCOLOR = 4

# Define base structure for consistency across all C types
class PackedLittleEndianStructure(ctypes.LittleEndianStructure):
    # This attribute forces the compiler/ctypes to ignore standard alignment rules
    # and pack the fields exactly as defined, byte after byte.
    _pack_ = 1
    pass

# ----------------------------------------------------------------------
# FileID structure definition (from HEADER.CPY from FastCAD's v6 SDK)
# DBVERSION	equ	24		;correct current database
#
# FileID		struc
# ProgID		SBYTE	'FCW (FastCAD for Windows) '	;26 bytes
# VerText		SBYTE	versionStr	                    ;version # as text (always 4 bytes)
# VerTextS	    SBYTE	SubVer		                    ;beta version (always 3 bytes)
# 		        SBYTE	'           '	                ;11 bytes
# 		        SBYTE	13,10,26	                    ;terminating chars for DOS Type cmd.
# DBVer		    SBYTE	DBVERSION
# Compressed	SBYTE	0		                        ;1 = compressed file
# 		        SBYTE	78 dup (0)	                    ;filler
# 		        SBYTE	0FFh		                    ;end marker (total 128 bytes)
# FileID		ends
# 
# sizeFileID	equ	128		                            ;sizeof(FileID) treats
# ----------------------------------------------------------------------
class FileID(PackedLittleEndianStructure):
    _fields_ = [
        ("ProgID",     ctypes.c_char * 26),  # 'FCW (FastCAD for Windows) '
        ("VerText",    ctypes.c_char * 4),   # version # as text
        ("VerTextS",   ctypes.c_char * 2),   # subversion (changed to 2 bytes based on looking at a real file)
        ("Padding",   ctypes.c_char * 12),  # padding (changed to 12 bytes based on looking at a real file)
        ("Special",    ctypes.c_char * 3),
        ("DBVer",      ctypes.c_ubyte),      # DBVERSION
        ("Compressed", ctypes.c_ubyte),      # 1 = compressed file
        ("Filler",     ctypes.c_char * 78), # filler
        ("EndMarker",  ctypes.c_ubyte),      # 0xFF end marker
    ]

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.ProgID = b'FCW (FastCAD for Windows) '
        self.VerText = b'6.20'
        # need to embedd a CR/LF/EOF sequence in the VerTextS field
        self.VerTextS = b'.0'
        self.Padding = bytes([0x0D, 0x0A, 0x1A, 0x69, 0x6E, 0x67, 0x20, 0x66, 0x69, 0x6C, 0x65, 0x2E])  # Based on real file
        self.Special = bytes([13, 10, 26])  # CR, LF, EOF
        self.DBVer = 24
        self.Filler = bytes([    # Based on real file analysis, not sure if it matters what goes here
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x7E, 
            0x7E, 0x7E, 0x7E, 0x7E, 0x7E, 0x7E, 0x7E, 0x7E, 0x7E, 0x7E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        ])
        self.Compressed = 0  # Not compressed for now, although we know how to do that if needed (it uses PKWare compression)
        self.EndMarker = 0xFF

    
    def __repr__(self):
        return (
            f"FileID(ProgID='{self.ProgID.decode('utf-8').strip(chr(0))}', "
            f"VerText='{self.VerText.decode('utf-8').strip(chr(0))}', "
            f"DBVer={self.DBVer}, Compressed={self.Compressed})"
        )

# CSTUFF Entity Flags (EFlags)
EF_ERASED = 0x80        # (old 5.163 files only!)
EF_Mark = 0x20        # entity is highlighted
EF_NOSL = 0x10        # ignore sublist (const SYMREF)

EF_CSREF = 0x08        # color = color of SYMREF
EF_Share = 0x04        # shared use flag

EF_A1 = 0x02        # arrow at T=1 end
EF_A0 = 0x01        # arrow at T=0 end

EF2_NOUTL = 0x01  # no outline on fill

class CSTUFF(PackedLittleEndianStructure):
    _fields_ = [
        ("ERLen",   ctypes.c_int),          # entity record length
        ("EType",   ctypes.c_ubyte),        # entity type code
        ("EFlags",  ctypes.c_char),         # erase/select bits
        ("EFlags2", ctypes.c_char),         # extra flags
        ("EColor",  ctypes.c_ubyte),        # entity color
        ("EColor2", ctypes.c_ubyte),        # fill (2nd) color
        ("EThick",  ctypes.c_char),         # pen thickness 0..25.4 mm
        ("WPlane",  ctypes.c_short),        # workplane (0 = XY plane)
        ("ELayer",  ctypes.c_short),        # layer
        ("ELStyle", ctypes.c_short),        # line style (0=solid)
        ("GroupID", ctypes.c_short),        # group id (0 = not grouped)
        ("EFStyle", ctypes.c_short),        # fill style (0=hollow)
        ("LWidth",  ctypes.c_float),        # line width
        ("Tag",     ctypes.c_int),          # entity tag id
    ]

    def __init__(self, len, type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ERLen = len
        self.EType = type
        # Assign default values common in CC3+
        self.EFlags = b'\x00'
        self.EFlags2 = b'\x00'
        self.EColor = 224
        self.EColor2 = 224
        self.EThick = b'\x00'
        self.WPlane = 0
        self.ELayer = 256
        self.ELStyle = 0
        self.GroupID = 0
        self.EFStyle = 1
        self.LWidth = 0.0
        self.Tag = 0  # TODO: Assign unique tags as needed?  Currently using 0 works, but not sure whether CC3+ is detecting that and assigning a real tag later. Need to check the debugger to confirm.


    def __repr__(self):
        return (
            f"CSTUFF(ERLen={self.ERLen}, EType={self.EType}, EFlags={ord(self.EFlags)}, "
            f"EFlags2={ord(self.EFlags2)}, "
            f"EColor={self.EColor}, EColor2={self.EColor2}, Ethick={self.EThick}, WPlane={self.WPlane}, "
            f"ELayer={self.ELayer}, ELStyle={self.ELStyle}, GroupID={self.GroupID}, "
            f"EFStyle={self.EFStyle}, LWidth={self.LWidth}, Tag={self.Tag})"
        )

class GPOINT3(PackedLittleEndianStructure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
    ]
    def __repr__(self):
        return f"GPOINT3(x={self.x}, y={self.y}, z={self.z})"

class GPOINT2(PackedLittleEndianStructure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
    ]
    def __repr__(self):
        return f"GPOINT2(x={self.x}, y={self.y})"

class SYMDEF(PackedLittleEndianStructure):
    _fields_ = [
        ("CStuff",  CSTUFF),              
        ("Low",     GPOINT3),            # lowest x,y,z extents coordinate
        ("Hi",      GPOINT3),            # highest x,y,z extents coordinate
        ("Flags",   ctypes.c_uint),      # options/status flags
        ("SName",   ctypes.c_char * 32), # ANSIZ symbol name
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        CSTUFF.__init__(self.CStuff, ctypes.sizeof(SYMDEF), ET_SYMDEF)
    
    def __repr__(self):
        return (
            f"SYMDEF(\n"
            f"  CStuff={self.CStuff},\n"
            f"  Low={self.Low!r},\n"
            f"  Hi={self.Hi!r},\n"
            f"  Flags={self.Flags},\n"
            f"  SName='{self.SName.decode('utf-8').strip(chr(0))}'\n"
            f")"
        )

class Marker(PackedLittleEndianStructure):
    _fields_ = [
        ("ERLen", ctypes.c_uint32), 
        ("MType", ctypes.c_ubyte), 
    ]
    
    def __init__(self, m_type_value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set the length field to the total size of the structure in bytes
        self.ERLen = ctypes.sizeof(Marker) # Which is 5 bytes
        self.MType = m_type_value
    
    def __repr__(self):
        return f"Marker(ERLen={self.ERLen}, MType={self.MType})"

class Marker0(Marker):
    def __init__(self, *args, **kwargs):
        # Call the parent's init, passing 0 as the specific MType value
        super().__init__(m_type_value=0, *args, **kwargs)

class Marker1(Marker):
    def __init__(self, *args, **kwargs):
        # Call the parent's init, passing 1 as the specific MType value
        super().__init__(m_type_value=1, *args, **kwargs)

class RESINFO(PackedLittleEndianStructure):
    _fields_ = [
        ("Present", ctypes.c_int),   # BOOL (Typically a 32-bit integer in Windows C/C++)
        ("width",   ctypes.c_uint),  # UINT (Typically a 32-bit unsigned integer)
        ("height",  ctypes.c_uint),  # UINT (Typically a 32-bit unsigned integer)
    ]
    
    def __repr__(self):
        return f"RESINFO(Present={bool(self.Present)}, width={self.width}, height={self.height})"

class PICTR(PackedLittleEndianStructure):
    _fields_ = [
        ("CStuff",    CSTUFF),               # entity properties (nested struct)
        ("XPId",      ctypes.c_ushort),      # unsigned short
        ("XType",     ctypes.c_char),        # char

        ("Version",   ctypes.c_uint32),      # DWORD (maps to c_uint32 or c_ulong)
        ("Flags",     ctypes.c_uint32),      # DWORD

        ("Mode",      ctypes.c_uint32),      # IMGXFRMODE

        ("bmwid",     ctypes.c_uint32),      # DWORD (actual bitmap size)
        ("bmhgt",     ctypes.c_uint32),

        ("Cen",       GPOINT2),              # Bitmap center (nested struct)
        ("Bearing",   ctypes.c_float),
        ("RWid",      ctypes.c_float),
        ("RHgt",      ctypes.c_float),       # real size * 0.5    # TODO: Confirm halving this value is necessary.  This implementation does not do it.

        ("TColor",    ctypes.c_uint),        # UINT (maps to c_uint)
        ("Alpha",     ctypes.c_int),         # int

        ("ResInfo",   RESINFO * RESINFO_COUNT), 
        ("Reserve",   ctypes.c_uint32 * 32), # DWORD[32]
        ("BMPName",   ctypes.c_char * 256),  # char[256]
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        CSTUFF.__init__(self.CStuff, ctypes.sizeof(PICTR), ET_XP)
        self.XPId = XPID_PICTR
        self.XType = XT_PICTR
        self.Version = PICTR_VERSION
        self.Flags = PF_NO_OUTLINE | PF_RESINFO_ONLY1 | PF_RESINFO_VALID
        self.Mode = IMGXFRMODE.IMGX_ALPHA 

    def __repr__(self):
        name = self.BMPName.decode('utf-8')
        return (
            f"PICTR(XPId={self.XPId}, Version={self.Version}, "
            f"Bearing={self.Bearing:.2f}, Alpha={self.Alpha}, "
            f"BMPName='{name}')"
        )

class SYMINFO(PackedLittleEndianStructure):
    _fields_ = [
        ("CStuff",         CSTUFF),               # entity properties
        ("XPId",           ctypes.c_ushort),      # XP ID # for custom entity SVC
        ("XType",          ctypes.c_char),        # entity sub-type (if needed)

        ("Version",        ctypes.c_short),       # structure version number
        ("Flags",          ctypes.c_uint32),      # basic flags (SF_*)
        ("Flags2",         ctypes.c_uint32),      # extended flags (currently unused, should always be 0)

        ("RotA",           ctypes.c_float),       # random range (only valid if TF_ROTATE)
        ("RotB",           ctypes.c_float),       # random offset angle (only valid if TF_ROTATE)
        ("TFlags",         ctypes.c_uint32),      # random transform flags (TF_*)
        
        # The comments assigned to these scale variables seem suspect - like they are swapped in some places,
        # but the comments are directly copied from XT_Entities.h
        ("ScaleAX",        ctypes.c_float),       # random X scale (only valid if TF_SCALE)
        ("ScaleBX",        ctypes.c_float),       # random Y scale (only valid if TF_SCALE)
        ("ScaleAY",        ctypes.c_float),       # random independent X scale (only valid if TF_SCALE and TF_SCALE_XY)
        ("ScaleBY",        ctypes.c_float),       # random independent Y scale (only valid if TF_SCALE and TF_SCALE_XY)

        ("ShearA",         ctypes.c_float),       # random shear factor min (only valid if TF_SHEAR)
        ("ShearB",         ctypes.c_float),       # random shear factor max (only valid if TF_SHEAR)
        ("unused1",        ctypes.c_char * 4),    # unused

        ("OffsetHiX",      ctypes.c_float),       # random offset X high value (only valid if TF_OFFSET)
        ("OffsetHiY",      ctypes.c_float),       # random offset Y high value (only valid if TF_OFFSET)
        ("OffsetLowX",     ctypes.c_float),       # random offset X low value (only valid if TF_OFFSET)
        ("OffsetLowY",     ctypes.c_float),       # random offset Y low value (only valid if TF_OFFSET)

        ("GFlags",         ctypes.c_uint32),      # Group flags (SGF_*)
        ("unused2",        ctypes.c_char * 49),   # unused

        ("Sheet",          ctypes.c_char * 64),   # sheet name on which to place symbol
        ("DrawToolName",   ctypes.c_char * 128),  # drawing tool name that is this "symbol"
        ("unused3",        ctypes.c_char * 64),   # reserved for future expansion
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        CSTUFF.__init__(self.CStuff, ctypes.sizeof(SYMINFO), ET_XP)
        self.XPId = XPID_SYMINFO
        self.XType = XT_SYMINFO
        self.Version = SYMINFO_VERSION

    def __repr__(self):
        # Decode specific string fields
        sheet_name = self.Sheet.decode('utf-8').strip(chr(0))
        tool_name = self.DrawToolName.decode('utf-8').strip(chr(0))
        
        return (
            f"SYMINFO(\n"
            f"  Len={self.CStuff.ERLen}, Version={self.Version}, Flags={hex(self.Flags)},\n"
            f"  RotA={self.RotA:.2f}, ScaleAX={self.ScaleAX:.2f},\n"
            f"  Sheet='{sheet_name}',\n"
            f"  DrawToolName='{tool_name}'\n"
            f")"
        )

# ----------------------------------------------------------------------
# The Simple Symbol Definition Structure
#
# Used in a symbol catalog for a standard single-image symbol.
# ----------------------------------------------------------------------

class SimpleSymbol(PackedLittleEndianStructure):
    """
    A single object containing all required structures in the specified sequence:
    SYMDEF, Marker0, PICTR, SYMINFO, and Marker1.
    """
    _fields_ = [
        ("symbol_definition", SYMDEF),
        ("start_marker",      Marker0),
        ("picture_info",      PICTR),
        ("symbol_info",       SYMINFO),
        ("end_marker",        Marker1),
    ]

    def __init__(self, name, file, isGroup, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        SYMDEF.__init__(self.symbol_definition)
        self.symbol_definition.SName = name.encode('utf-8')
        x, y = png_dimensions(file)
        self.symbol_definition.Hi.x = float(x)/40
        self.symbol_definition.Hi.y = float(y)/40
        self.symbol_definition.Hi.z = float(0)
        self.symbol_definition.Low.x = float(0)
        self.symbol_definition.Low.y = float(0)
        self.symbol_definition.Low.z = float(0)

        Marker0.__init__(self.start_marker)

        PICTR.__init__(self.picture_info)
        self.picture_info.BMPName = file.encode('utf-8')
        self.picture_info.RWid = float(x)/40
        self.picture_info.RHgt = float(y)/40

        SYMINFO.__init__(self.symbol_info)
        self.symbol_info.ScaleAX = 1.0
        self.symbol_info.ScaleAY = 1.0
        self.symbol_info.ScaleBX = 1.0
        self.symbol_info.ScaleBY = 1.0
        if isGroup:
            self.symbol_info.Flags |= SF_GROUPED
            self.symbol_info.GFlags |=  SGF_RANDOM

        Marker1.__init__(self.end_marker)

    def __repr__(self):
        return (
            f"SimpleSymbol(\n"
            f"  Symbol Name: '{self.symbol_definition.SName.decode('utf-8').strip(chr(0))}',\n"
            f"  Start Marker MType: {self.start_marker.MType},\n"
            f"  Picture BMP Name: '{self.picture_info.BMPName.decode('utf-8').strip(chr(0))}',\n"
            f"  End Marker MType: {self.end_marker.MType}\n"
            f")"
        )

# ----------------------------------------------------------------------
# The Varicolor Symbol Definition Structure
# 
# Used in a symbol catalog for a varicolor symbol that uses two images,
# where the second image is a mask used to apply the selected color to
# the first image.
# ----------------------------------------------------------------------

class VaricolorSymbol(PackedLittleEndianStructure):
    """
    A single object containing all required structures in the specified sequence:
    SYMDEF, Marker0, PICTR, SYMINFO, and Marker1.
    """
    _fields_ = [
        ("symbol_definition", SYMDEF),
        ("start_marker",      Marker0),
        ("picture1_info",      PICTR),
        ("picture2_info",      PICTR),
        ("symbol_info",       SYMINFO),
        ("end_marker",        Marker1),
    ]

    def __init__(self, name, file1, file2, isGroup, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        SYMDEF.__init__(self.symbol_definition)
        self.symbol_definition.SName = name.encode('utf-8')
        x, y = png_dimensions(file1)
        self.symbol_definition.Hi.x = float(x)/40
        self.symbol_definition.Hi.y = float(y)/40
        self.symbol_definition.Hi.z = float(0)
        self.symbol_definition.Low.x = float(0)
        self.symbol_definition.Low.y = float(0)
        self.symbol_definition.Low.z = float(0)

        Marker0.__init__(self.start_marker)
        
        PICTR.__init__(self.picture1_info)
        self.picture1_info.BMPName = file1.encode('utf-8')
        self.picture1_info.RWid = float(x)/40
        self.picture1_info.RHgt = float(y)/40
        
        PICTR.__init__(self.picture2_info)
        self.picture2_info.BMPName = file2.encode('utf-8')
        x, y = png_dimensions(file2)
        self.picture2_info.RWid = float(x)/40
        self.picture2_info.RHgt = float(y)/40
        self.picture2_info.CStuff.EFlags = EF_CSREF   # This is needed to make the 2nd PNG the varicolor mask
        
        SYMINFO.__init__(self.symbol_info)
        self.symbol_info.Flags = SF_VARICOLOR
        self.symbol_info.ScaleAX = 1.0
        self.symbol_info.ScaleAY = 1.0
        self.symbol_info.ScaleBX = 1.0
        self.symbol_info.ScaleBY = 1.0
        if isGroup:
            self.symbol_info.Flags |= SF_GROUPED
            self.symbol_info.GFlags |= SGF_VARICOLOR | SGF_RANDOM
        
        Marker1.__init__(self.end_marker)

    def __repr__(self):
        return (
            f"VaricolorSymbol(\n"
            f"  Symbol Name: '{self.symbol_definition.SName.decode('utf-8').strip(chr(0))}',\n"
            f"  Start Marker MType: {self.start_marker.MType},\n"
            f"  Picture BMP1 Name: '{self.picture1_info.BMPName.decode('utf-8').strip(chr(0))}',\n"
            f"  Picture BMP2 Name: '{self.picture2_info.BMPName.decode('utf-8').strip(chr(0))}',\n"
            f"  End Marker MType: {self.end_marker.MType}\n"
            f")"
        )

# --- Test Code ---
# This block will ONLY run if you execute this file directly, which is not the normal use case.
# This is just for testing purposes for confirming different data structures were built correctly.
if __name__ == "__main__":
    # Instantiate a Marker 0
    m0 = Marker0()
    print(f"Instantiated m0: {m0!r}")
    print(f"m0 raw bytes: {bytes(m0).hex()}")

    print("-" * 20)

    # Instantiate a Marker 1
    m1 = Marker1()
    print(f"Instantiated m1: {m1!r}")
    print(f"m1 raw bytes: {bytes(m1).hex()}")

    # Verification: The length should always be 5, and MType 0 or 1
    assert m0.ERLen == 5
    assert m0.MType == 0
    assert m1.ERLen == 5
    assert m1.MType == 1

    #############################################################

    # Create an instance of the structure in Python
    entity = CSTUFF(ctypes.sizeof(CSTUFF), 5)
    entity.EFlags = b'\x01' # Char fields expect bytes type input in Python 3
    entity.EColor = 255
    entity.WPlane = 0
    entity.ELayer = 10
    entity.LWidth = 2.5
    entity.Tag = 999

    # Print the structure instance using the custom __repr__
    print(f"Structure instance: {entity}")

    # Print the total size of the structure in bytes
    print(f"Size of CSTUFF structure: {ctypes.sizeof(CSTUFF)} bytes")

    # To treat the structure as raw bytes (e.g., to write to a file or send over a socket):
    raw_bytes = bytes(entity)
    print(f"Raw bytes representation (first 20): {raw_bytes[:20].hex()}")

    #############################################################

    symbol_def = SYMDEF()

    # Assigning values to nested structures
    symbol_def.CStuff.Tag = 500
    symbol_def.Low.x = -10.0
    symbol_def.Low.y = -10.0
    symbol_def.Low.z = 0.0

    # Assigning values to top-level fields
    symbol_def.Flags = 0x01 | 0x02

    # Assigning a string to a fixed-size char array
    # We must encode the Python string to bytes and use [:] to fit it in the array buffer
    name_bytes = b"MyAwesomeSymbol67890123456789012"
    symbol_def.SName = name_bytes 

    print(symbol_def)
    raw_bytes = bytes(symbol_def)
    print(f"Raw bytes representation: {raw_bytes[:88].hex()}")
    print(f"\nTotal size of SYMDEF structure: {ctypes.sizeof(SYMDEF)} bytes")

    #############################################################

    print("--- Running PICTR test demonstration ---")

    pic = PICTR()
    
    # Initialize some nested structure fields
    pic.CStuff.Tag = 99
    pic.Cen.x = 150.25
    pic.Cen.y = 200.5
    pic.XPId = 5
    pic.Version = 3
    pic.Bearing = 90.0
    pic.ResInfo[0].Present = 1 # Set the first element in the array
    pic.ResInfo[0].width = 1920

    # Assigning a string to the fixed-size char array using .value
    pic.BMPName = b"C:\\images\\floorplan.bmp"

    print(f"Total size of PICTR structure (packed): {ctypes.sizeof(PICTR)} bytes")
    print("\nInitialized PICTR object:")
    print(pic)
    
    # Example of accessing the reserve array data (currently zeros)
    print(f"\nReserve array bytes (first 8): {bytes(pic.Reserve)[:8].hex()}")

    # Assertions for basic verification
    assert pic.Cen.x == 150.25
    assert pic.BMPName == b"C:\\images\\floorplan.bmp"
    assert ctypes.sizeof(PICTR) == 511
    print("\nAssertions passed.")

    #############################################################

    print("--- Running SYMINFO test demonstration ---")

    sym = SYMINFO()
    sym.Version = 1
    sym.Flags = 0x1
    sym.RotA = 0.5
    sym.ScaleAX = 1.0
    sym.GFlags = 0xFF

    sym.Sheet = b"First Floor Plan"
    sym.DrawToolName = b"Advanced Symbol Tool v2"

    print(f"Total size of SYMINFO structure (packed): {ctypes.sizeof(SYMINFO)} bytes")
    print("\nInitialized SYMINFO object:")
    print(sym)

    ### PICTR analysis from a bytes array dump
    data = bytes([
        0xFF, 0x01, 0x00, 0x00, 0x04, 0x08, 0x00, 0xE0, 0xE0, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 
        0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0E, 0x2C, 0x00, 0x00, 0x04, 0xA0, 0x01, 0x00, 
        0x00, 0x00, 0x00, 0x0D, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x66, 0x66, 0x59, 0x41, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x66, 
        0x66, 0x59, 0x41, 0x33, 0x33, 0x4F, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x43, 
        0x3A, 0x5C, 0x55, 0x73, 0x65, 0x72, 0x73, 0x5C, 0x6E, 0x6F, 0x73, 0x70, 0x61, 0x5C, 0x44, 0x6F, 
        0x77, 0x6E, 0x6C, 0x6F, 0x61, 0x64, 0x73, 0x5C, 0x68, 0x65, 0x72, 0x65, 0x2D, 0x74, 0x68, 0x65, 
        0x72, 0x65, 0x2D, 0x62, 0x65, 0x2D, 0x6D, 0x6F, 0x6E, 0x73, 0x74, 0x65, 0x72, 0x73, 0x2D, 0x31, 
        0x2E, 0x31, 0x5C, 0x48, 0x65, 0x72, 0x65, 0x20, 0x54, 0x68, 0x65, 0x72, 0x65, 0x20, 0x42, 0x65, 
        0x20, 0x4D, 0x6F, 0x6E, 0x73, 0x74, 0x65, 0x72, 0x73, 0x20, 0x31, 0x2E, 0x31, 0x5C, 0x50, 0x4E, 
        0x47, 0x5C, 0x57, 0x6F, 0x6F, 0x64, 0x70, 0x65, 0x63, 0x6B, 0x65, 0x72, 0x20, 0x57, 0x68, 0x61, 
        0x6C, 0x65, 0x20, 0x76, 0x61, 0x72, 0x69, 0x5F, 0x30, 0x32, 0x2E, 0x70, 0x6E, 0x67, 0x00, 0x00, 
        0x6E, 0x67, 0x00, 0x67, 0x00, 0x6E, 0x67, 0x00, 0x6E, 0x67, 0x00, 0x00, 0x00, 0x67, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    ])
    pic_from_data = PICTR.from_buffer_copy(data)
    print(f"\nPICTR created from byte array dump:")
    # Print out every field for verification
    print(pic_from_data.CStuff)
    print(f"XPId: {pic_from_data.XPId}")
    print(f"BMPName: {pic_from_data.BMPName.decode('utf-8').strip(chr(0))}")
    print(f"Version: {pic_from_data.Version}")
    print(f"Flags: {pic_from_data.Flags}")
    print(f"Mode: {pic_from_data.Mode}")
    print(f"bmwid: {pic_from_data.bmwid}")
    print(f"bmhgt: {pic_from_data.bmhgt}")
    print(f"Cen: {pic_from_data.Cen}")
    print(f"Bearing: {pic_from_data.Bearing}")
    print(f"RWid: {pic_from_data.RWid}")
    print(f"RHgt: {pic_from_data.RHgt}")
    print(f"TColor: {pic_from_data.TColor}")
    print(f"Alpha: {pic_from_data.Alpha}")
    for i, res in enumerate(pic_from_data.ResInfo):
        print(f"ResInfo[{i}]: {res}")
    print(f"Reserve (first 8 DWORDs): {[hex(x) for x in pic_from_data.Reserve[:8]]}")

    print(f"\nTotal size of PICTR structure from data: {ctypes.sizeof(PICTR)} bytes")
    assert pic_from_data.CStuff.ERLen == ctypes.sizeof(PICTR)
    #############################################################
    # SYMINFO from bytes dump
    data = bytes([
        0x96, 0x01, 0x00, 0x00, 0x04, 0x00, 0x00, 0xE0, 0xE0, 0x00, 0x00, 0x00, 0x07, 0x01, 0x00, 0x00, 
        0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x73, 0x2C, 0x00, 0x00, 0x0B, 0xA0, 0x61, 0x01, 
        0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x3F, 0x00, 0x00, 0x80, 0x3F, 0x00, 0x00, 0x80, 
        0x3F, 0x00, 0x00, 0x80, 0x3F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    ])

    sym_from_data = SYMINFO.from_buffer_copy(data)
    print(f"\nSYMINFO created from byte array dump:")
    # Print out every field for verification
    print(sym_from_data)
    print(f"\nTotal size of SYMINFO structure from data: {ctypes.sizeof(SYMINFO)} bytes")
    print(sym_from_data.CStuff)
    print(f"XPId: {sym_from_data.XPId}")
    print(f"Version: {sym_from_data.Version}")
    print(f"Flags: {hex(sym_from_data.Flags)}")
    print(f"Flags2: {hex(sym_from_data.Flags2)}")
    print(f"RotA: {sym_from_data.RotA}")
    print(f"RotB: {sym_from_data.RotB}")
    print(f"TFlags: {hex(sym_from_data.TFlags)}")
    print(f"ScaleAX: {sym_from_data.ScaleAX}")
    print(f"ScaleBX: {sym_from_data.ScaleBX}")
    print(f"ScaleAY: {sym_from_data.ScaleAY}")
    print(f"ScaleBY: {sym_from_data.ScaleBY}")
    print(f"ShearA: {sym_from_data.ShearA}")
    print(f"ShearB: {sym_from_data.ShearB}")
    print(f"OffsetHiX: {sym_from_data.OffsetHiX}")
    print(f"OffsetHiY: {sym_from_data.OffsetHiY}")
    print(f"OffsetLowX: {sym_from_data.OffsetLowX}")
    print(f"OffsetLowY: {sym_from_data.OffsetLowY}")
    print(f"GFlags: {hex(sym_from_data.GFlags)}")
    print(f"Sheet: {sym_from_data.Sheet.decode('utf-8').strip(chr(0))}")
    print(f"DrawToolName: {sym_from_data.DrawToolName.decode('utf-8').strip(chr(0))}")
    assert sym_from_data.CStuff.ERLen == ctypes.sizeof(SYMINFO)
    #############################################################
    # Ensure a dummy file exists for testing
    if not os.path.exists("test_image.png"):
        print("Please place a 'test_image.png' in the current directory.")
    else:
        width, height = png_dimensions("test_image.png")
        if width is not None:
            print(f"The dimensions of test_image.png are: {width}x{height} pixels.")
    ############################################################
    # Test SYMDEF layout
    data = bytes([
        0x58, 0x00, 0x00, 0x00, 0x1C, 0x00, 0x00, 0xE0, 0xE0, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 
        0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x2C, 0x00, 0x00, 0x81, 0xF3, 0x17, 0xB4, 
        0x38, 0x33, 0x4F, 0xC0, 0x00, 0x00, 0x00, 0x00, 0x66, 0x66, 0xD9, 0x41, 0x33, 0x33, 0x4F, 0x40, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x57, 0x6F, 0x6F, 0x64, 0x70, 0x65, 0x63, 0x6B, 
        0x65, 0x72, 0x20, 0x57, 0x68, 0x61, 0x6C, 0x65, 0x20, 0x76, 0x61, 0x72, 0x69, 0x00, 0x00, 0x00, 
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    ])
    symdef_from_data = SYMDEF.from_buffer_copy(data)
    print(f"\nSYMDEF created from byte array dump:")
    print(symdef_from_data)
    print(f"\nTotal size of SYMDEF structure from data: {ctypes.sizeof(SYMDEF)} bytes")
    assert symdef_from_data.CStuff.ERLen == ctypes.sizeof(SYMDEF)
    #############################################################

    