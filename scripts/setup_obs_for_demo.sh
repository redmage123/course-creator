#!/bin/bash
"""
Setup OBS Studio for Demo Recording

This script:
1. Creates OBS configuration directory
2. Sets up WebSocket server
3. Configures recording settings
4. Creates a Browser Capture scene
"""

OBS_CONFIG_DIR="$HOME/.config/obs-studio"
mkdir -p "$OBS_CONFIG_DIR/basic/scenes"
mkdir -p "$OBS_CONFIG_DIR/basic/profiles/Untitled/logs"

# Create basic configuration
cat > "$OBS_CONFIG_DIR/global.ini" << 'EOF'
[General]
FirstRun=false

[BasicWindow]
geometry=@ByteArray(\x1\xd9\xd0\xcb\0\x3\0\0\0\0\0\0\0\0\0\0\0\0\a\x7f\0\0\x4\x37\0\0\0\0\0\0\0\0\0\0\a\x7f\0\0\x4\x37\0\0\0\0\0\0\0\0\a\x80\0\0\0\0\0\0\0\0\0\0\a\x7f\0\0\x4\x37)

[OBSWebSocket]
ServerEnabled=true
ServerPort=4455
AlertsEnabled=false
AuthRequired=false
ServerPassword=
EOF

# Create profile with recording settings
cat > "$OBS_CONFIG_DIR/basic/profiles/Untitled/basic.ini" << 'EOF'
[Output]
Mode=Simple

[SimpleOutput]
RecFormat2=mp4
RecEncoder=x264
RecQuality=Stream
FilePath=$HOME/course-creator/frontend/static/demo/videos
RecTracks=1

[Video]
BaseCX=1920
BaseCY=1080
OutputCX=1920
OutputCY=1080
FPSType=0
FPSCommon=30

[Audio]
SampleRate=48000

[AdvOut]
RecType=Standard
RecFormat=mp4
RecEncoder=obs_x264
EOF

# Create a basic scene with browser source
cat > "$OBS_CONFIG_DIR/basic/scenes/Untitled.json" << 'EOF'
{
    "current_scene": "Demo Scene",
    "current_transition": "Fade",
    "scene_order": [
        {
            "name": "Demo Scene"
        }
    ],
    "scenes": [
        {
            "name": "Demo Scene",
            "settings": {},
            "sources": [
                {
                    "name": "Browser",
                    "settings": {
                        "width": 1920,
                        "height": 1080,
                        "fps": 30,
                        "shutdown": false,
                        "restart_when_active": false,
                        "css": "body { cursor: url('data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\"><path fill=\"red\" stroke=\"white\" stroke-width=\"2\" d=\"M3,3 L3,27 L11,19 L15,28 L18,27 L14,18 L23,18 Z\"/></svg>') 0 0, auto !important; }"
                    },
                    "type": "browser_source",
                    "volume": 1.0
                }
            ]
        }
    ],
    "transitions": [
        {
            "name": "Fade",
            "settings": {},
            "type": "fade_transition"
        }
    ]
}
EOF

echo "✅ OBS configuration created at $OBS_CONFIG_DIR"
echo ""
echo "Next steps:"
echo "1. Start OBS Studio: obs --startrecording (will enable WebSocket server)"
echo "2. Configure WebSocket in OBS: Tools > WebSocket Server Settings"
echo "3. Enable WebSocket server on port 4455 without password"
echo "4. Run the Playwright demo script"
EOF

chmod +x "$OBS_CONFIG_DIR/../setup_obs_for_demo.sh"
