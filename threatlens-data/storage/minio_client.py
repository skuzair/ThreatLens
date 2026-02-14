"""
ThreatLens AI - MinIO Object Storage Client
Handles evidence storage (videos, pcaps, files, screenshots)
"""

from minio import Minio
from minio.error import S3Error
from io import BytesIO
import os
import logging
from datetime import timedelta
from typing import Optional, BinaryIO
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MinIOClient:
    """Wrapper for MinIO object storage operations"""
    
    def __init__(self, endpoint=None, access_key=None, secret_key=None, bucket=None, secure=False):
        """
        Initialize MinIO client
        
        Args:
            endpoint: MinIO server endpoint (default from env)
            access_key: Access key (default from env)
            secret_key: Secret key (default from env)
            bucket: Default bucket name (default from env)
            secure: Use HTTPS (default False for local)
        """
        self.endpoint = endpoint or os.getenv('MINIO_ENDPOINT', 'localhost:9000')
        self.access_key = access_key or os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = secret_key or os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        self.bucket = bucket or os.getenv('MINIO_BUCKET', 'threatlens-evidence')
        self.secure = secure or os.getenv('MINIO_SECURE', 'false').lower() == 'true'
        
        self.client = None
        self._connect()
    
    def _connect(self):
        """Establish connection to MinIO server"""
        try:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
            logger.info(f"Connected to MinIO at {self.endpoint}")
            
            # Create bucket if it doesn't exist
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Created bucket: {self.bucket}")
            else:
                logger.info(f"Using existing bucket: {self.bucket}")
                
        except S3Error as e:
            logger.error(f"Failed to connect to MinIO: {e}")
            raise
    
    def upload_file(self, file_path: str, object_name: str, content_type: str = 'application/octet-stream') -> str:
        """
        Upload a file to MinIO
        
        Args:
            file_path: Local file path to upload
            object_name: Object name in bucket (path/to/file.ext)
            content_type: MIME type of the file
            
        Returns:
            MinIO URI: minio://bucket/object_name
        """
        try:
            # Calculate file hash for integrity
            file_hash = self._calculate_file_hash(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Upload file
            self.client.fput_object(
                self.bucket,
                object_name,
                file_path,
                content_type=content_type,
                metadata={
                    'sha256': file_hash,
                    'original_path': file_path
                }
            )
            
            minio_uri = f"minio://{self.bucket}/{object_name}"
            logger.info(f"Uploaded {file_path} to {minio_uri} (size: {file_size} bytes, hash: {file_hash[:16]}...)")
            return minio_uri
            
        except S3Error as e:
            logger.error(f"Failed to upload {file_path}: {e}")
            raise
    
    def upload_bytes(self, data: bytes, object_name: str, content_type: str = 'application/octet-stream') -> str:
        """
        Upload bytes data to MinIO
        
        Args:
            data: Bytes data to upload
            object_name: Object name in bucket
            content_type: MIME type
            
        Returns:
            MinIO URI
        """
        try:
            data_stream = BytesIO(data)
            data_hash = hashlib.sha256(data).hexdigest()
            
            self.client.put_object(
                self.bucket,
                object_name,
                data_stream,
                length=len(data),
                content_type=content_type,
                metadata={'sha256': data_hash}
            )
            
            minio_uri = f"minio://{self.bucket}/{object_name}"
            logger.info(f"Uploaded {len(data)} bytes to {minio_uri}")
            return minio_uri
            
        except S3Error as e:
            logger.error(f"Failed to upload bytes to {object_name}: {e}")
            raise
    
    def download_file(self, object_name: str, file_path: str) -> str:
        """
        Download a file from MinIO
        
        Args:
            object_name: Object name in bucket
            file_path: Local path to save file
            
        Returns:
            Local file path
        """
        try:
            self.client.fget_object(
                self.bucket,
                object_name,
                file_path
            )
            logger.info(f"Downloaded {object_name} to {file_path}")
            return file_path
            
        except S3Error as e:
            logger.error(f"Failed to download {object_name}: {e}")
            raise
    
    def download_bytes(self, object_name: str) -> bytes:
        """
        Download object as bytes
        
        Args:
            object_name: Object name in bucket
            
        Returns:
            File contents as bytes
        """
        try:
            response = self.client.get_object(self.bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"Downloaded {len(data)} bytes from {object_name}")
            return data
            
        except S3Error as e:
            logger.error(f"Failed to download {object_name}: {e}")
            raise
    
    def get_presigned_url(self, object_name: str, expiry_hours: int = 24) -> str:
        """
        Generate a presigned URL for temporary access
        
        Args:
            object_name: Object name in bucket
            expiry_hours: URL expiry time in hours
            
        Returns:
            Presigned URL
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket,
                object_name,
                expires=timedelta(hours=expiry_hours)
            )
            logger.info(f"Generated presigned URL for {object_name} (expires in {expiry_hours}h)")
            return url
            
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL for {object_name}: {e}")
            raise
    
    def delete_object(self, object_name: str) -> bool:
        """
        Delete an object from MinIO
        
        Args:
            object_name: Object name to delete
            
        Returns:
            True if successful
        """
        try:
            self.client.remove_object(self.bucket, object_name)
            logger.info(f"Deleted object: {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Failed to delete {object_name}: {e}")
            return False
    
    def list_objects(self, prefix: str = '', recursive: bool = True) -> list:
        """
        List objects in bucket
        
        Args:
            prefix: Filter objects by prefix
            recursive: List recursively
            
        Returns:
            List of object names
        """
        try:
            objects = self.client.list_objects(
                self.bucket,
                prefix=prefix,
                recursive=recursive
            )
            object_names = [obj.object_name for obj in objects]
            logger.info(f"Found {len(object_names)} objects with prefix '{prefix}'")
            return object_names
            
        except S3Error as e:
            logger.error(f"Failed to list objects: {e}")
            return []
    
    def object_exists(self, object_name: str) -> bool:
        """
        Check if an object exists
        
        Args:
            object_name: Object name to check
            
        Returns:
            True if exists
        """
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error:
            return False
    
    def get_object_info(self, object_name: str) -> dict:
        """
        Get object metadata
        
        Args:
            object_name: Object name
            
        Returns:
            Dictionary with metadata
        """
        try:
            stat = self.client.stat_object(self.bucket, object_name)
            return {
                'object_name': stat.object_name,
                'size': stat.size,
                'last_modified': stat.last_modified,
                'etag': stat.etag,
                'content_type': stat.content_type,
                'metadata': stat.metadata
            }
        except S3Error as e:
            logger.error(f"Failed to get info for {object_name}: {e}")
            return {}
    
    @staticmethod
    def _calculate_file_hash(file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def parse_minio_uri(uri: str) -> tuple:
        """
        Parse MinIO URI into bucket and object name
        
        Args:
            uri: MinIO URI (minio://bucket/path/to/object)
            
        Returns:
            Tuple of (bucket, object_name)
        """
        if not uri.startswith('minio://'):
            raise ValueError(f"Invalid MinIO URI: {uri}")
        
        parts = uri.replace('minio://', '').split('/', 1)
        bucket = parts[0]
        object_name = parts[1] if len(parts) > 1 else ''
        
        return bucket, object_name


# Singleton instance
_minio_client_instance = None


def get_minio_client() -> MinIOClient:
    """Get singleton MinIO client instance"""
    global _minio_client_instance
    if _minio_client_instance is None:
        _minio_client_instance = MinIOClient()
    return _minio_client_instance


if __name__ == '__main__':
    """Test MinIO client"""
    import tempfile
    
    client = get_minio_client()
    
    # Test upload/download
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("ThreatLens AI - Test Evidence File\n")
        f.write("This is a test upload to MinIO object storage.\n")
        temp_file = f.name
    
    try:
        # Upload test file
        uri = client.upload_file(temp_file, 'test/evidence.txt', content_type='text/plain')
        print(f"✓ Uploaded: {uri}")
        
        # Get presigned URL
        url = client.get_presigned_url('test/evidence.txt', expiry_hours=1)
        print(f"✓ Presigned URL (1h expiry): {url[:80]}...")
        
        # Download file
        download_path = tempfile.mktemp(suffix='.txt')
        client.download_file('test/evidence.txt', download_path)
        print(f"✓ Downloaded to: {download_path}")
        
        # List objects
        objects = client.list_objects('test/')
        print(f"✓ Objects in 'test/': {objects}")
        
        # Clean up
        client.delete_object('test/evidence.txt')
        os.remove(temp_file)
        os.remove(download_path)
        print("✓ Cleanup complete")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")