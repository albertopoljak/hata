__all__ = ()

from scarletio import IgnoreCaseString
from scarletio.web_common.headers import AUTHORIZATION as HEADER_AUTHORIZATION


LAVALINK_KEY_STATS_UPTIME = 'uptime'
LAVALINK_KEY_STATS_PLAYER_COUNT = 'players'
LAVALINK_KEY_STATS_PLAYING_PLAYER_COUNT = 'playingPlayers'

LAVALINK_KEY_STATS_MEMORY = 'memory'
LAVALINK_KEY_STATS_MEMORY_FREE = 'free'
LAVALINK_KEY_STATS_MEMORY_USED = 'used'
LAVALINK_KEY_STATS_MEMORY_ALLOCATED = 'allocated'
LAVALINK_KEY_STATS_MEMORY_RESERVABLE = 'reservable'

LAVALINK_KEY_STATS_CPU = 'cpu'
LAVALINK_KEY_STATS_CPU_CORES = 'cores'
LAVALINK_KEY_STATS_CPU_SYSTEM_LOAD = 'systemLoad'
LAVALINK_KEY_STATS_CPU_LAVALINK_LOAD = 'lavalinkLoad'

LAVALINK_KEY_STATS_FRAME = 'frameStats'
LAVALINK_KEY_STATS_FRAME_SENT = 'sent'
LAVALINK_KEY_STATS_FRAME_NULLED = 'nulled'
LAVALINK_KEY_STATS_FRAME_DEFICIT = 'deficit'


LAVALINK_KEY_THRESHOLD_MS = 'thresholdMs'
LAVALINK_KEY_GUILD_ID = 'guildId'
LAVALINK_KEY_SESSION_ID = 'sessionId'
LAVALINK_KEY_VOICE_SERVER_UPDATE_EVENT = 'event'
LAVALINK_KEY_PAUSE = 'pause'
LAVALINK_KEY_POSITION_MS = 'position'
LAVALINK_KEY_START_TIME = 'startTime'
LAVALINK_KEY_END_TIME = 'endTime'
LAVALINK_KEY_NO_REPLACE = 'noReplace'
LAVALINK_KEY_TRACK = 'track'
LAVALINK_KEY_PLAYER_STATE = 'state'
LAVALINK_KEY_EVENT_TYPE = 'type'
LAVALINK_KEY_END_REASON = 'reason'
LAVALINK_KEY_EXCEPTION_REASON_DEPRECATED = 'error'
LAVALINK_KEY_EXCEPTION_REASON_OBJECT = 'exception'
LAVALINK_KEY_EXCEPTION_REASON_OBJECT_MESSAGE = 'message'
LAVALINK_KEY_EXCEPTION_REASON_OBJECT_SEVERITY = 'severity'
LAVALINK_KEY_WEBSOCKET_CLOSE_CODE = 'code'
LAVALINK_KEY_WEBSOCKET_CLOSE_REASON = 'reason'
LAVALINK_KEY_WEBSOCKET_CLOSE_BY_REMOTE = 'byRemote'
LAVALINK_KEY_NODE_RESUME_KEY = 'key'
LAVALINK_KEY_TRACKS = 'tracks'
LAVALINK_KEY_PLAYLIST = 'playlistInfo'
LAVALINK_KEY_PLAYLIST_NAME = 'name'
LAVALINK_KEY_PLAYLIST_SELECTED_TRACK_INDEX = 'selectedTrack'


LAVALINK_KEY_FILTER_EQUALIZER = 'equalizer'
LAVALINK_KEY_FILTER_EQUALIZER_BAND = 'band'
LAVALINK_KEY_FILTER_EQUALIZER_GAIN = 'gain'

LAVALINK_KEY_FILTER_KARAOKE = 'karaoke'
LAVALINK_KEY_FILTER_KARAOKE_LEVEL = 'level'
LAVALINK_KEY_FILTER_KARAOKE_MONO_LEVEL = 'monoLevel'
LAVALINK_KEY_FILTER_KARAOKE_FILTER_BAND = 'filterBand'
LAVALINK_KEY_FILTER_KARAOKE_FILTER_WIDTH = 'filterWidth'

LAVALINK_KEY_FILTER_TIMESCALE = 'timescale'
LAVALINK_KEY_FILTER_TIMESCALE_PITCH = 'pitch'
LAVALINK_KEY_FILTER_TIMESCALE_RATE = 'rate'
LAVALINK_KEY_FILTER_TIMESCALE_SPEED = 'speed'


LAVALINK_KEY_FILTER_TREMOLO = 'tremolo'
LAVALINK_KEY_FILTER_TREMOLO_DEPTH = 'depth'
LAVALINK_KEY_FILTER_TREMOLO_FREQUENCY = 'frequency'


LAVALINK_KEY_FILTER_VIBRATO = 'vibrato'
LAVALINK_KEY_FILTER_VIBRATO_DEPTH = 'depth'
LAVALINK_KEY_FILTER_VIBRATO_FREQUENCY = 'frequency'

LAVALINK_KEY_FILTER_ROTATION = 'rotation'
LAVALINK_KEY_FILTER_ROTATION_ROTATION = 'rotationHz'

LAVALINK_KEY_FILTER_DISTORTION = 'distortion'
LAVALINK_KEY_FILTER_DISTORTION_COS_OFFSET = 'cosOffset'
LAVALINK_KEY_FILTER_DISTORTION_COS_SCALE = 'cosScale'
LAVALINK_KEY_FILTER_DISTORTION_SIN_OFFSET = 'sinOffset'
LAVALINK_KEY_FILTER_DISTORTION_SIN_SCALE = 'sinScale'
LAVALINK_KEY_FILTER_DISTORTION_TAN_OFFSET = 'tanOffset'
LAVALINK_KEY_FILTER_DISTORTION_TAN_SCALE = 'tanScale'
LAVALINK_KEY_FILTER_DISTORTION_OFFSET = 'offset'
LAVALINK_KEY_FILTER_DISTORTION_SCALE = 'scale'


LAVALINK_KEY_FILTER_CHANNEL_MIX = 'channelMix'
LAVALINK_KEY_FILTER_CHANNEL_MIX_LEFT_TO_LEFT = 'leftToLeft'
LAVALINK_KEY_FILTER_CHANNEL_MIX_LEFT_TO_RIGHT = 'leftToRight'
LAVALINK_KEY_FILTER_CHANNEL_MIX_RIGHT_TO_LEFT = 'rightToLeft'
LAVALINK_KEY_FILTER_CHANNEL_MIX_RIGHT_TO_RIGHT = 'rightToRight'


LAVALINK_KEY_FILTER_LOW_PASS = 'lowPass'
LAVALINK_KEY_FILTER_LOW_PASS_SMOOTHING = 'smoothing'


LAVALINK_KEY_GATEWAY_OPERATION_STATS = 'stats'
LAVALINK_KEY_GATEWAY_OPERATION_PLAYER_UPDATE = 'playerUpdate'
LAVALINK_KEY_GATEWAY_OPERATION_EVENT = 'event'

LAVALINK_KEY_FILTER_VOLUME = 'volume'


LAVALINK_KEY_NODE_OPERATION = 'op'
LAVALINK_KEY_NODE_OPERATION_VOICE_UPDATE = 'voiceUpdate'
LAVALINK_KEY_NODE_OPERATION_PLAYER_DESTROY = 'destroy'
LAVALINK_KEY_NODE_OPERATION_PLAYER_STOP = 'stop'
LAVALINK_KEY_NODE_OPERATION_PLAYER_PAUSE = 'pause'
LAVALINK_KEY_NODE_OPERATION_PLAYER_SEEK = 'seek'
LAVALINK_KEY_NODE_OPERATION_PLAYER_EDIT_BANDS = 'equalizer'
LAVALINK_KEY_NODE_OPERATION_PLAYER_PLAY = 'play'
LAVALINK_KEY_NODE_OPERATION_PLAYER_FILTER = 'filters'
LAVALINK_KEY_NODE_OPERATION_SET_RESUME_KEY = 'configureResuming'

LAVALINK_KEY_EVENT_TRACK_END = 'TrackEndEvent'
LAVALINK_KEY_EVENT_TRACK_EXCEPTION = 'TrackExceptionEvent'
LAVALINK_KEY_EVENT_TRACK_START = 'TrackStartEvent'
LAVALINK_KEY_EVENT_TRACK_STUCK = 'TrackStuckEvent'
LAVALINK_KEY_EVENT_PLAYER_WEB_SOCKET_CLOSED = 'WebSocketClosedEvent'


LAVALINK_KEY_TRACK_BASE64 = 'track'
LAVALINK_KEY_TRACK_DICT = 'info'
LAVALINK_KEY_TRACK_IDENTIFIER = 'identifier'
LAVALINK_KEY_TRACK_SEEKABLE = 'isSeekable'
LAVALINK_KEY_TRACK_AUTHOR = 'author'
LAVALINK_KEY_TRACK_DURATION_MS = 'length'
LAVALINK_KEY_TRACK_IS_STREAM = 'isStream'
LAVALINK_KEY_TRACK_TITLE = 'title'
LAVALINK_KEY_TRACK_URL = 'uri'
LAVALINK_KEY_TRACK_POSITION_MS = 'position'


LAVALINK_KEY_ROUTEPLANNER_TYPE = 'class'
LAVALINK_KEY_ROUTEPLANNER_TYPE_ROTATING_IP = 'RotatingIpRoutePlanner'
LAVALINK_KEY_ROUTEPLANNER_TYPE_NANO_IP = 'NanoIpRoutePlanner'
LAVALINK_KEY_ROUTEPLANNER_TYPE_ROTATING_NANO_IP = 'RotatingNanoIpRoutePlanner'
LAVALINK_KEY_ROUTEPLANNER_OBJECT = 'details'
LAVALINK_KEY_ROUTEPLANNER_OBJECT_IP_BLOCK = 'ipBlock'
LAVALINK_KEY_ROUTEPLANNER_OBJECT_IP_BLOCK_TYPE = 'type'
LAVALINK_KEY_ROUTEPLANNER_OBJECT_IP_BLOCK_SIZE_STRING = 'size'
LAVALINK_KEY_ROUTEPLANNER_OBJECT_FAILING_ADDRESSES = 'failingAddresses'
LAVALINK_KEY_ROUTEPLANNER_OBJECT_FAILING_ADDRESS_ADDRESS = 'address'
LAVALINK_KEY_ROUTEPLANNER_OBJECT_FAILING_ADDRESS_UNIX_TIME = 'failingTimestamp'
LAVALINK_KEY_ROUTEPLANNER_OBJECT_BLOCK_INDEX_STRING = 'blockIndex'
LAVALINK_KEY_ROUTEPLANNER_OBJECT_CURRENT_ADDRESS_INDEX_STRING = 'currentAddressIndex'
LAVALINK_KEY_ROUTEPLANNER_OBJECT_ROTATE_INDEX_STRING = 'rotateIndex'
LAVALINK_KEY_ROUTEPLANNER_OBJECT_IP_INDEX_STRING = 'ipIndex'
LAVALINK_KEY_ROUTEPLANNER_OBJECT_CURRENT_ADDRESS = 'currentAddress'

HEADER_USER_ID = IgnoreCaseString('User-Id')
HEADER_CLIENT_NAME = IgnoreCaseString('Client-Name')
HEADER_SHARD_COUNT = IgnoreCaseString('Num-Shards')
HEADER_RESUME_KEY = IgnoreCaseString('Resume-Key')


LAVALINK_BAND_COUNT = 15
