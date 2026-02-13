from minio import Minio
from minio.error import S3Error
from datetime import timedelta
import os
from config import settings


class EvidenceService:
    """Service for managing evidence files in MinIO"""
    
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                print(f"✅ Created MinIO bucket: {self.bucket}")
        except S3Error as e:
            print(f"❌ Error creating bucket: {e}")
    
    def upload_evidence(self, incident_id: str, file_path: str, evidence_type: str) -> str:
        """
        Upload evidence file to MinIO
        Returns the object name (path in MinIO)
        """
        try:
            filename = os.path.basename(file_path)
            object_name = f"{incident_id}/{evidence_type}/{filename}"
            
            self.client.fput_object(self.bucket, object_name, file_path)
            print(f"✅ Uploaded evidence: {object_name}")
            
            return object_name
        except S3Error as e:
            print(f"❌ Error uploading evidence: {e}")
            raise
    
    def get_presigned_url(self, object_name: str, expires_hours: int = 1) -> str:
        """
        Generate presigned URL for temporary access to evidence
        Default expiry: 1 hour
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket,
                object_name,
                expires=timedelta(hours=expires_hours)
            )
            return url
        except S3Error as e:
            print(f"❌ Error generating presigned URL: {e}")
            raise
    
    def download_evidence(self, object_name: str, local_path: str):
        """Download evidence file from MinIO to local path"""
        try:
            self.client.fget_object(self.bucket, object_name, local_path)
            print(f"✅ Downloaded evidence: {object_name} -> {local_path}")
        except S3Error as e:
            print(f"❌ Error downloading evidence: {e}")
            raise
    
    def list_evidence(self, incident_id: str) -> list:
        """List all evidence files for an incident"""
        try:
            objects = self.client.list_objects(
                self.bucket,
                prefix=f"{incident_id}/",
                recursive=True
            )
            return [obj.object_name for obj in objects]
        except S3Error as e:
            print(f"❌ Error listing evidence: {e}")
            return []


# Global instance
evidence_service = EvidenceService()
