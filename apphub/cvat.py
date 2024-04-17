import os
import subprocess as sp

import gradio as gr
from apphub.app import App, AppOption


class Cvat(App):

    docker_images = [
        "postgres",
        "redis",
        "apache/kvrocks",
        "cvat/server",
        "cvat/ui",
        "traefik",
        "openpolicyagent/opa",
        "clickhouse/clickhouse-server",
        "timberio/vector",
        "grafana/grafana-oss",
    ]

    class CvatOption(AppOption):
        source_directory: str = None

    cfg: CvatOption

    @property
    def key(self) -> str:
        """该属性作为 app 的唯一标识，注意这里只能用数字、字母、下划线、横杠（减号）组成
        key 会被很多地方使用，例如 key 也会被充当为 package_name
        """
        return "cvat"

    @property
    def op_port(self) -> int:
        return 30009

    @property
    def port(self) -> int:
        """表示该 App 需要占用的端口号，推荐在 20000 至 30000 之间选择一个端口"""
        return 8080

    @property
    def name(self) -> str:
        """应用的名称，展示给用户看的"""
        return "CVAT 标注工具"

    @property
    def icon(self) -> str:
        """应用 icon"""
        return "https://featurize-public.oss-cn-beijing.aliyuncs.com/apps/cvat.png"

    def render_installation_page(self) -> "gr.Blocks":
        with gr.Blocks() as demo:
            gr.Markdown(
                """# 安装 CVAT 应用

标注应用，可直接调用使用 Featurize 的算力。
"""
            )
            install_location = self.render_install_location(allow_work=False)
            version = gr.Dropdown(
                choices=["2.11.3"], label="安装的版本", value="2.11.3"
            )
            self.render_installation_button(inputs=[install_location, version])
            self.render_log()
        return demo

    def installation(self, install_location, version):
        super().installation(install_location, version)
        self.cfg.source_directory = os.path.join(install_location, "cvat")
        self.execute_command(
            f"git clone --depth 1 --branch v{self.cfg.version} https://github.com/cvat-ai/cvat"
        )
        self.execute_command("docker compose pull", self.cfg.source_directory)
        self.save_app_config()
        self.app_installed()

    def start(self):
        output = sp.check_output(["docker", "image", "ls"], stderr=sp.STDOUT).decode()
        for image_name in self.docker_images:
            if image_name in output:
                continue
            image_name_file = image_name.replace("/", "_")
            self.execute_command(
                f"docker load < {image_name_file}.tar.gz",
                self.cfg.docker_image_directory,
            )
        self.execute_command(
            f"CVAT_HOST='{self.host}' docker compose up",
            self.cfg.source_directory,
            daemon=True,
        )
        self.logger.info("docker compose up successed")
        self.app_started()

    def close(self):
        self.execute_command(f"docker compose down", self.cfg.source_directory)

    def uninstall(self):
        super().uninstall()
        for image_name in self.docker_images:
            self.execute_command(f"docker rmi {image_name}", cwd="~")


def main():
    return Cvat()
