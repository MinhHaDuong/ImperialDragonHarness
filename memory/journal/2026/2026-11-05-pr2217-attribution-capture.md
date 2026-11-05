# PR 2217 attribution capture

On 2026-11-05, PR #2217 merged after Gaze and the second merge gate passed. The post-merge `attribution_record.py --capture-unit pr:2217` call reported `not derivable: writer model` and `not derivable: writer`, and did not write a review-attribution record. The model identity was not available to the capturing session. The review and gate records remain on `refs/notes/review`; attribution capture is pending recovery of the writer's observed model identity.
