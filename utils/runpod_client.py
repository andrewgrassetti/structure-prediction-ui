"""
RunPod serverless API client for Boltz-2 structure prediction jobs.
"""
import time
import requests


RUNPOD_BASE_URL = "https://api.runpod.ai/v2"
DEFAULT_POLL_INTERVAL = 5  # seconds
DEFAULT_MAX_WAIT = 3600    # 1 hour


class RunPodClient:
    """Client for the RunPod serverless REST API."""

    def __init__(self, api_key: str, endpoint_id: str):
        if not api_key:
            raise ValueError("RunPod API key must not be empty.")
        if not endpoint_id:
            raise ValueError("RunPod endpoint ID must not be empty.")
        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.base_url = f"{RUNPOD_BASE_URL}/{endpoint_id}"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Job submission
    # ------------------------------------------------------------------

    def submit_job(self, input_payload: dict) -> dict:
        """Submit an async prediction job to the RunPod endpoint.

        Parameters
        ----------
        input_payload:
            Dictionary placed under the ``"input"`` key of the RunPod
            request body.

        Returns
        -------
        dict
            RunPod response containing at least ``id`` and ``status``.
        """
        url = f"{self.base_url}/run"
        body = {"input": input_payload}
        try:
            response = requests.post(url, json=body, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as exc:
            raise RuntimeError(
                f"RunPod job submission failed (HTTP {exc.response.status_code}): "
                f"{exc.response.text}"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"RunPod job submission error: {exc}") from exc

    # ------------------------------------------------------------------
    # Status polling
    # ------------------------------------------------------------------

    def get_job_status(self, job_id: str) -> dict:
        """Fetch the current status of a job.

        Parameters
        ----------
        job_id:
            The RunPod job ID returned by :meth:`submit_job`.

        Returns
        -------
        dict
            RunPod status response (contains ``status`` and optionally
            ``output`` or ``error``).
        """
        url = f"{self.base_url}/status/{job_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as exc:
            raise RuntimeError(
                f"RunPod status check failed (HTTP {exc.response.status_code}): "
                f"{exc.response.text}"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"RunPod status check error: {exc}") from exc

    def wait_for_completion(
        self,
        job_id: str,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
        max_wait: int = DEFAULT_MAX_WAIT,
        progress_callback=None,
    ) -> dict:
        """Poll until the job completes or times out.

        Parameters
        ----------
        job_id:
            RunPod job ID.
        poll_interval:
            Seconds between status polls.
        max_wait:
            Maximum seconds to wait before raising a timeout error.
        progress_callback:
            Optional callable ``(status: str) -> None`` called on each poll.

        Returns
        -------
        dict
            Final RunPod status response.
        """
        start = time.time()
        while True:
            status_data = self.get_job_status(job_id)
            status = status_data.get("status", "unknown")
            if progress_callback:
                progress_callback(status)
            if status in ("COMPLETED", "FAILED", "CANCELLED"):
                return status_data
            if time.time() - start > max_wait:
                raise TimeoutError(
                    f"Job {job_id} did not complete within {max_wait} seconds."
                )
            time.sleep(poll_interval)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def cancel_job(self, job_id: str) -> dict:
        """Request cancellation of a running job."""
        url = f"{self.base_url}/cancel/{job_id}"
        try:
            response = requests.post(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"RunPod job cancellation error: {exc}") from exc

    @staticmethod
    def format_status(status: str) -> str:
        """Return a human-readable label for a RunPod status string."""
        mapping = {
            "IN_QUEUE": "⏳ Queued",
            "IN_PROGRESS": "🔄 Running",
            "COMPLETED": "✅ Completed",
            "FAILED": "❌ Failed",
            "CANCELLED": "🚫 Cancelled",
        }
        return mapping.get(status.upper(), status)
