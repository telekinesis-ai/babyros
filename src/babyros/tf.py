import numpy as np
import threading
import time
from collections import deque
from scipy.spatial.transform import Rotation as R
from babyros.node import Publisher, Subscriber


class TFUtils:
    """
    Utility functions for handling transformations.
    """
    @staticmethod
    def create_matrix(trans, quat):
        """Create a 4x4 matrix from translation [x,y,z] and quat [x,y,z,w]"""
        mat = np.eye(4)
        mat[:3, :3] = R.from_quat(quat).as_matrix()
        mat[:3, 3] = trans
        return mat

    @staticmethod
    def interpolate(mat1, mat2, t1, t2, target_t):
        """Linearly interpolate between two 4x4 matrices at target_t."""
        alpha = (target_t - t1) / (t2 - t1)
        # Interpolate translation
        trans = (1 - alpha) * mat1[:3, 3] + alpha * mat2[:3, 3]
        # Slerp for rotation
        r1 = R.from_matrix(mat1[:3, :3])
        r2 = R.from_matrix(mat2[:3, :3])
        # Simple lerp of rotation for BabyROS (use Slerp for pro version)
        rot = R.from_matrix(r1.as_matrix() * (1-alpha) + r2.as_matrix() * alpha)
        
        res = np.eye(4)
        res[:3, :3] = rot.as_matrix()
        res[:3, 3] = trans
        return res

class TransformBroadcaster:
    """
    Broadcasts transform messages over the /tf topic.
    """
    def __init__(self):
        self._pub = Publisher("/tf")

    def send_transform(self, parent, child, translation, rotation, timestamp=None):
        """
        rotation should be [x, y, z, w] quaternion.
        """
        msg = {
            "parent": parent,
            "child": child,
            "translation": list(translation),
            "rotation": list(rotation),
            "timestamp": timestamp or time.time()
        }
        self._pub.publish(msg)

class TFBuffer:
    """
    Buffer for storing and managing transform frames.
    """
    def __init__(self, cache_time=10.0):
        self.cache_time = cache_time
        self._frames = {} # {child: deque([(time, parent, matrix), ...])}
        self._lock = threading.Lock()
        self._sub = Subscriber("/tf", self._callback)

    def _callback(self, msg):
        with self._lock:
            child = msg['child']
            if child not in self._frames:
                self._frames[child] = deque()
            
            mat = TFUtils.create_matrix(msg['translation'], msg['rotation'])
            entry = (msg['timestamp'], msg['parent'], mat)
            
            # Keep buffer sorted by time and prune old data
            buffer = self._frames[child]
            buffer.append(entry)
            while buffer and (time.time() - buffer[0][0] > self.cache_time):
                buffer.popleft()

    def lookup_transform(self, target_frame, source_frame, target_time=None):
        """Returns target_T_source at target_time."""
        if target_time is None:
            target_time = time.time()

        with self._lock:
            # 1. Trace path to root for both frames
            path_s = self._get_path(source_frame, target_time)
            path_t = self._get_path(target_frame, target_time)

            # 2. Find Common Ancestor
            common = None
            for f in path_s:
                if f in path_t:
                    common = f
                    break
            
            if not common:
                raise RuntimeError(f"No link between {source_frame} and {target_frame}")

            # 3. Chain matrices: target_T_source = target_T_common * common_T_source
            # Note: common_T_source is (source_T_common)^-1
            T_common_source = self._chain(source_frame, common, target_time)
            T_common_target = self._chain(target_frame, common, target_time)
            
            return np.linalg.inv(T_common_target) @ T_common_source

    def _get_path(self, frame, t):
        path = [frame]
        curr = frame
        while curr in self._frames:
            # Get the parent from the closest timestamp
            _, parent, _ = self._get_closest(curr, t)
            path.append(parent)
            curr = parent
            if curr == "world": break # Safety
        return path

    def _get_closest(self, frame, t):
        """Finds the transform for a frame closest to time t."""
        buffer = self._frames[frame]
        if not buffer: 
            raise ValueError(f"Empty buffer for {frame}")
        
        # Simple approach: find closest. 
        # (A pro version would interpolate between the two surrounding timestamps)
        closest = min(buffer, key=lambda x: abs(x[0] - t))
        return closest

    def _chain(self, start, end, t):
        """Computes transform from start UP to end at time t."""
        res = np.eye(4)
        curr = start
        while curr != end:
            timestamp, parent, mat = self._get_closest(curr, t)
            res = mat @ res 
            curr = parent
        return res