import os
import kfp.dsl as dsl
from kfp.dsl import PipelineVolume

# To compile the pipeline:
#   dsl-compile --py pipeline.py --output pipeline.tar.gz

WORKSPACE = '/workspace'
PROJECT_ROOT = os.path.join(WORKSPACE, 'tensorflow_lprnet_test')


def git_clone_op(repo_url: str):
    image='quangphammessi/project_hub:latest'
    
    commands = [
        f"git clone {repo_url} {PROJECT_ROOT}",
        f"cd {PROJECT_ROOT}"]

    volume_op = dsl.VolumeOp(
        name='create pipeline volume',
        resource_name='pipeline-pvc',
        modes=["ReadWriteOnce"],
        size='3Gi'
    )

    op = dsl.ContainerOp(
        name='git clone',
        image=image,
        command=['sh'],
        arguments=['-c', ' && '.join(commands)],
        container_kwargs={'image_pull_policy': 'IfNotPresent'},
        pvolumes={WORKSPACE: volume_op.volume}
    )

    return op