import os
import tempfile
import unittest
from clipforge.database.db_manager import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        # Use an in-memory SQLite database for fast isolated unit tests
        self.db_fd, self.db_filename = tempfile.mkstemp()
        self.db = DatabaseManager(db_path=self.db_filename)

    def tearDown(self):
        # Release SQLite references and force garbage collection to release file locks on Windows
        self.db = None
        import gc
        gc.collect()
        os.close(self.db_fd)
        if os.path.exists(self.db_filename):
            os.remove(self.db_filename)

    def test_settings_get_set(self):
        self.db.set_setting("test_key", "hello_world")
        val = self.db.get_setting("test_key")
        self.assertEqual(val, "hello_world")
        
        # Test default
        self.assertEqual(self.db.get_setting("non_existent", "fallback"), "fallback")

    def test_video_crud(self):
        video_id = self.db.add_video("My Test Video", file_path="C:/videos/test.mp4", duration=120.5)
        self.assertTrue(video_id > 0)
        
        video = self.db.get_video(video_id)
        self.assertIsNotNone(video)
        self.assertEqual(video["title"], "My Test Video")
        self.assertEqual(video["duration"], 120.5)
        self.assertEqual(video["status"], "ingested")
        
        # Update status
        self.db.update_video_status(video_id, "transcribed")
        video = self.db.get_video(video_id)
        self.assertEqual(video["status"], "transcribed")
        
        # Delete video
        self.db.delete_video(video_id)
        self.assertIsNone(self.db.get_video(video_id))

    def test_transcripts(self):
        video_id = self.db.add_video("Transcription Test")
        
        # Add transcript segment
        self.db.add_transcript_segment(
            video_id=video_id,
            start_time=1.5,
            end_time=5.2,
            text="Hello testing transcripts",
            speaker="Speaker 1",
            words=[{"word": "Hello", "start": 1.5, "end": 2.0}]
        )
        
        segments = self.db.get_transcripts_for_video(video_id)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0]["text"], "Hello testing transcripts")
        self.assertEqual(len(segments[0]["words"]), 1)
        self.assertEqual(segments[0]["words"][0]["word"], "Hello")

    def test_clips_crud(self):
        video_id = self.db.add_video("Clips Test")
        clip_id = self.db.add_clip(
            video_id=video_id,
            title="Clip 1 Highlight",
            start_time=10.0,
            end_time=25.0,
            viral_score=85,
            hook="Insane trick!",
            description="Detailed highlight description"
        )
        
        self.assertTrue(clip_id > 0)
        clip = self.db.get_clip(clip_id)
        self.assertIsNotNone(clip)
        self.assertEqual(clip["viral_score"], 85)
        self.assertEqual(clip["status"], "detected")
        
        # Update status
        self.db.update_clip_status(clip_id, "rendered", export_path="C:/exports/clip1.mp4")
        clip = self.db.get_clip(clip_id)
        self.assertEqual(clip["status"], "rendered")
        self.assertEqual(clip["export_path"], "C:/exports/clip1.mp4")


if __name__ == "__main__":
    unittest.main()
