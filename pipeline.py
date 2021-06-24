import os
import kfp.dsl as dsl
from kfp.dsl import PipelineVolume

# To compile the pipeline:
#   dsl-compile --py pipeline.py --output pipeline.tar.gz

WORKSPACE = '/workspace'
PROJECT_ROOT = os.path.join(WORKSPACE, 'tensorflow_lprnet_test')
CONDA_PYTHON_CMD = '/opt/conda/envs/kubeflow-lpr/bin/python'


def git_clone_op(repo_url: str):
    image='alpine/git:latest'
    
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

def train_op(image: str, pvolumn: PipelineVolume):
    return dsl.ContainerOp(
        name='training',
        image=image,
        command=[CONDA_PYTHON_CMD, f'{PROJECT_ROOT}/main.py'],
        arguments=['-m', 'train'],
        container_kwargs={'image_pull_policy': 'IfNotPresent'},
        pvolumes={"/workspace": pvolumn}
    )

@dsl.pipeline(
    name='License Plate Recognition Training Pipeline',
    description='License Plate Recognition Training Pipeline to be executed on KubeFlow.'
)
def training_pipeline(image: str='quangphammessi/project_hub:latest',
                        repo_url: str='https://github.com/quangphammessi/tensorflow_lprnet_test',
                        data_dir: str='/workspace'):
    git_clone = git_clone_op(repo_url=repo_url)

    train = train_op(image=image, pvolumn=git_clone.pvolume)


if __name__ == '__main__':
    import kfp.compiler as compiler

    compiler.Compiler().compile(training_pipeline, __file__ + '.tar.gz')