import difflib  # For create_diff
import logging
import os
import subprocess
import sys
from pathlib import Path  # For apply_diff
from typing import TYPE_CHECKING, Dict, List, Optional


# Налаштування логування
logger = logging.getLogger(__name__)


# Try to import third-party libraries
try:
    from github import Github, GithubException
except ImportError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa: B007
    Github = None
    GithubException = None
    logger.warning("PyGithub не встановлено. Функціонал GitHub API буде недоступний.")

try:
    import patch as patch_ng
except ImportError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa: B007
    patch_ng = None
    logger.warning("Бібліотека 'patch-ng' не встановлена. Функціонал застосування diff-ів буде недоступний.")

if TYPE_CHECKING:
    # This avoids circular import issues at runtime but allows type hinting
    pass


class GitModule:
    """Модуль для взаємодії з Git-репозиторієм та GitHub API."""

    def __init__(
        self,
        repo_path: str,
        github_token: Optional[str] = None,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
    ) -> None:
        """Ініціалізує GitModule.

        Args:
            repo_path (str): Шлях до кореневої директорії Git-репозиторію.
            github_token (Optional[str]): Токен GitHub для взаємодії з API.
            repo_owner (Optional[str]): Власник репозиторію на GitHub.
            repo_name (Optional[str]): Назва репозиторію на GitHub.
        """
        self.repo_path = repo_path
        # Використовуємо прямі аргументи замість словника config
        self.github_token = github_token
        self.github_repo_owner = repo_owner
        self.github_repo_name = repo_name

        self.repo = None  # Екземпляр GitPython Repo
        self.github_client = None  # Екземпляр PyGithub Github

        self._initialize_repo()
        self._initialize_github_client()
        logger.info("GitModule ініціалізовано")

    def _initialize_repo(self) -> None:
        """Ініціалізує об'єкт GitPython Repo."""
        try:
            # Перевіряємо, чи є директорія Git-репозиторієм
            subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"], cwd=self.repo_path, check=True, capture_output=True
            )
            logger.info(f"Директорія '{self.repo_path}' вже є Git-репозиторієм.")
        except subprocess.CalledProcessError:
            logger.error(f"Директорія '{self.repo_path}' не є Git-репозиторієм. Ініціалізація неможлива.")
            sys.exit(1)
        except FileNotFoundError:  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa: B007  # noqa  # noqa: B007
            logger.error("Git не встановлено або не знайдено в PATH. Будь ласка, встановіть Git.")
            sys.exit(1)

    def _initialize_github_client(self) -> None:
        """Ініціалізує клієнт GitHub API, якщо надано токен."""
        if Github and self.github_token and self.github_repo_owner and self.github_repo_name:
            try:
                self.github_client = Github(self.github_token)
                user = self.github_client.get_user(self.github_repo_owner)
                self.repo = user.get_repo(self.github_repo_name)
                logger.info(
                    f"Успішно підключено до репозиторію GitHub: {self.github_repo_owner}/{self.github_repo_name}"
                )
            except GithubException as e:
                logger.error(f"Помилка підключення до GitHub API: {e}", exc_info=True)
                self.github_client = None
                self.repo = None
            except Exception as e:
                logger.error(f"Неочікувана помилка при ініціалізації GitHub клієнта: {e}", exc_info=True)
                self.github_client = None
                self.repo = None
        else:
            logger.warning(
                "Токен GitHub, власник репозиторію або назва репозиторію не надані. Функціонал GitHub API буде недоступний."
            )

    def _run_git_command(self, command: List[str], error_message: str) -> bool:
        """Виконує команду Git."""
        try:
            subprocess.run(command, cwd=self.repo_path, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"{error_message}: {e.stderr.decode()}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Неочікувана помилка при виконанні Git команди: {e}", exc_info=True)
            return False

    def get_current_branch(self) -> Optional[str]:
        """Повертає назву поточної гілки."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Не вдалося отримати поточну гілку: {e.stderr.decode()}", exc_info=True)
            return None

    def is_working_directory_clean(self) -> bool:
        """Перевіряє, чи робоча директорія чиста (без незбережених змін)."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"], cwd=self.repo_path, check=True, capture_output=True, text=True
            )
            return len(result.stdout.strip()) == 0
        except subprocess.CalledProcessError as e:
            logger.error(f"Помилка при перевірці чистоти робочої директорії: {e.stderr.decode()}", exc_info=True)
            return False

    def create_and_checkout_branch(self, branch_name: str) -> bool:
        """Створює нову гілку та переключається на неї."""
        if not self._run_git_command(
            ["git", "checkout", "-b", branch_name], f"Не вдалося створити та переключитися на гілку '{branch_name}'"
        ):
            return False
        logger.info(f"Створено та переключено на гілку '{branch_name}'.")
        return True

    def checkout_branch(self, branch_name: str) -> bool:
        """Переключається на існуючу гілку."""
        if not self._run_git_command(
            ["git", "checkout", branch_name], f"Не вдалося переключитися на гілку '{branch_name}'"
        ):
            return False
        logger.info(f"Переключено на гілку '{branch_name}'.")
        return True

    def delete_branch(self, branch_name: str) -> bool:
        """Видаляє гілку."""
        if not self._run_git_command(
            ["git", "branch", "-D", branch_name], f"Не вдалося видалити гілку '{branch_name}'"
        ):
            return False
        logger.info(f"Гілку '{branch_name}' видалено.")
        return True

    def add_all(self) -> bool:
        """Додає всі зміни до індексу."""
        if not self._run_git_command(["git", "add", "."], "Не вдалося додати всі зміни"):
            return False
        logger.info("Всі зміни додано до індексу.")
        return True

    def commit(self, message: str) -> bool:
        """Створює коміт."""
        if not self._run_git_command(
            ["git", "commit", "-m", message], f"Не вдалося створити коміт з повідомленням '{message}'"
        ):
            return False
        logger.info(f"Коміт створено: '{message}'.")
        return True

    def push(self, branch_name: str, remote: str = "origin") -> bool:
        """Виконує push змін до віддаленого репозиторію."""
        if not self._run_git_command(
            ["git", "push", remote, branch_name], f"Не вдалося виконати push гілки '{branch_name}' до '{remote}'"
        ):
            return False
        logger.info(f"Зміни успішно запушено до '{remote}/{branch_name}'.")
        return True

    def reset_file(self, file_path: str) -> bool:
        """Відкочує зміни у файлі до останнього коміту."""
        full_path = os.path.join(self.repo_path, file_path)
        if not os.path.exists(full_path):
            logger.warning(f"Файл '{full_path}' не існує, неможливо відкотити.")
            return False
        if not self._run_git_command(["git", "checkout", "--", file_path], f"Не вдалося відкотити файл '{file_path}'"):
            return False
        logger.info(f"Файл '{file_path}' відкочено до останнього коміту.")
        return True

    def create_pull_request(
        self, title: str, body: str, head_branch: str, base_branch: str
    ) -> Optional[Dict[str, object]]:
        """Створює Pull Request на GitHub.

        Args:
            title (str): Заголовок Pull Request.
            body (str): Опис Pull Request.
            head_branch (str): Гілка, з якої створюється PR (ваша гілка зі змінами).
            base_branch (str): Гілка, в яку створюється PR (наприклад, 'main' або 'develop').

        Returns:
            Optional[Dict[str, object]]: Словник з інформацією про створений PR (номер, URL) або None у разі помилки.
        """
        if not self.repo:
            logger.error("GitHub репозиторій не ініціалізовано. Неможливо створити Pull Request.")
            return None

        try:
            pull = self.repo.create_pull(title=title, body=body, head=head_branch, base=base_branch)
            logger.info(f"Pull Request #{pull.number} створено: {pull.html_url}")
            return {"number": pull.number, "url": pull.html_url}
        except GithubException as e:
            logger.error(
                f"Помилка GitHub API при створенні Pull Request: {e.data.get('message', str(e))}", exc_info=True
            )
        return None

    def merge_and_delete_branch(self, head_branch: str, base_branch: str, remote: str = "origin") -> Dict[str, object]:
        """Автоматично зливає гілку (head_branch) у базову гілку (base_branch).

        та видаляє head_branch локально та віддалено.

        Args:
            head_branch (str): Гілка, яку потрібно злити та видалити.
            base_branch (str): Базова гілка, в яку відбувається злиття.
            remote (str): Назва віддаленого репозиторію (зазвичай 'origin').

        Returns:
            Dict[str, object]: Результат операції злиття та видалення.
        """
        logger.info(f"Початок злиття '{head_branch}' у '{base_branch}' та подальшого видалення.")
        # current_branch = self.get_current_branch()  # Unused variable removed

        # 1. Переключитися на базову гілку
        if not self.checkout_branch(base_branch):
            return {"status": "error", "message": f"Не вдалося переключитися на базову гілку '{base_branch}'."}

        # 2. Злити гілку зі змінами
        if not self._run_git_command(
            ["git", "merge", head_branch], f"Не вдалося злити '{head_branch}' у '{base_branch}'. Можливі конфлікти."
        ):
            logger.error(
                f"Злиття гілки '{head_branch}' у '{base_branch}' завершилося з помилкою. Можливо, є конфлікти. Залишаюся на '{base_branch}'."
            )
            return {
                "status": "error",
                "message": f"Злиття гілки '{head_branch}' у '{base_branch}' не вдалося. Можливі конфлікти.",
            }
        logger.info(f"Гілку '{head_branch}' успішно злито у '{base_branch}'.")

        # 3. Видалити гілку локально
        self.delete_branch(head_branch)  # Логування вже є всередині методу

        # 4. Видалити гілку з віддаленого репозиторію
        if not self._run_git_command(
            ["git", "push", remote, "--delete", head_branch],
            f"Не вдалося видалити віддалену гілку '{head_branch}' з '{remote}'.",
        ):
            logger.warning(f"Не вдалося видалити віддалену гілку '{head_branch}'. Можливо, її вже немає.")

        return {"status": "success", "message": f"Гілку '{head_branch}' успішно злито у '{base_branch}' та видалено."}

    def create_tag(self, tag_name: str, message: str) -> bool:
        """Створює анотований тег у репозиторії.

        Args:
            tag_name (str): Назва тегу (наприклад, 'v1.0.0').
            message (str): Повідомлення для анотованого тегу.

        Returns:
            bool: True, якщо тег успішно створено, інакше False.
        """
        logger.info(f"Спроба створити тег '{tag_name}'...")
        command = ["git", "tag", "-a", tag_name, "-m", message]
        if not self._run_git_command(command, f"Не вдалося створити тег '{tag_name}'"):
            return False
        logger.info(f"Тег '{tag_name}' успішно створено.")
        return True

    def push_tags(self) -> bool:
        """Виконує push всіх тегів до віддаленого репозиторію."""
        logger.info("Спроба виконати push тегів...")
        command = ["git", "push", "--tags"]
        if not self._run_git_command(command, "Не вдалося виконати push тегів"):
            return False
        logger.info("Теги успішно запушено.")
        return True

    def get_latest_tag(self) -> Optional[str]:
        """Отримує останній тег у репозиторії на основі дати коміту."""
        try:
            # Сортуємо теги за датою коміту, на який вони вказують, у зворотному порядку
            command = ["git", "tag", "--sort=-creatordate"]
            result = subprocess.run(
                command, cwd=self.repo_path, check=True, capture_output=True, text=True, encoding="utf-8"
            )
            tags = result.stdout.strip().splitlines()
            if tags:
                latest_tag = tags[0]
                logger.info(f"Знайдено останній тег: {latest_tag}")
                return latest_tag
            else:
                logger.info("Теги не знайдено в репозиторії.")
                return None
        except (subprocess.CalledProcessError, Exception) as e:
            # Не є критичною помилкою, якщо тегів немає
            logger.warning(f"Не вдалося отримати останній тег: {e}")
            return None

    def get_commit_history(self, since_ref: Optional[str] = None, until_ref: str = "HEAD") -> List[Dict[str, str]]:
        """Отримує історію комітів у вигляді списку словників.

        Args:
            since_ref (Optional[str]): Початковий тег або коміт (не включається в результат).
                                       Якщо None, історія береться з першого коміту.
            until_ref (str): Кінцевий тег або коміт.

        Returns:
            List[Dict[str, str]]: Список комітів, де кожен коміт - це словник
                                  з ключами 'hash', 'author', 'date', 'subject'.
        """
        # Формат для git log, який легко парсити. Використовуємо рідкісний роздільник.
        log_format = "%H<--GIT_SEP-->%an<--GIT_SEP-->%ai<--GIT_SEP-->%s"

        # Визначаємо діапазон комітів
        commit_range = f"{since_ref}..{until_ref}" if since_ref else until_ref

        command = ["git", "log", f"--format={log_format}", commit_range]

        try:
            result = subprocess.run(
                command, cwd=self.repo_path, check=True, capture_output=True, text=True, encoding="utf-8"
            )

            history: List = []
            output = result.stdout.strip()
            if not output:
                return []

            for line in output.splitlines():
                parts = line.split("<--GIT_SEP-->")
                if len(parts) == 4:
                    history.append({"hash": parts[0], "author": parts[1], "date": parts[2], "subject": parts[3]})

            logger.info(f"Отримано {len(history)} комітів з діапазону '{commit_range}'.")
            return history
        except (subprocess.CalledProcessError, Exception) as e:
            logger.error(f"Не вдалося отримати історію комітів: {e}", exc_info=True)
            return []

    def create_diff(self, file_path: str, original_content: str, new_content: str) -> str:
        """Генерує unified diff між двома версіями вмісту файлу.

        Args:
            file_path (str): Шлях до файлу (використовується для заголовка diff).
            original_content (str): Оригінальний вміст файлу.
            new_content (str): Новий вміст файлу.

        Returns:
            str: Unified diff у вигляді рядка.
        """
        # difflib.unified_diff працює з списками рядків
        fromlines = original_content.splitlines(keepends=True)
        tolines = new_content.splitlines(keepends=True)

        # Генеруємо diff
        diff = difflib.unified_diff(
            fromlines,
            tolines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm="",  # Важливо, щоб не дублювати переноси рядків
        )
        return "".join(diff)

    def apply_diff(self, diff_content: str) -> Dict[str, object]:
        """Застосовує наданий diff до файлів у репозиторії.

        Args:
            diff_content (str): Вміст diff у стандартному форматі.

        Returns:
            Dict[str, object]: Результат застосування diff.
        """
        base_path = Path(self.repo_path).resolve()

        if not base_path.is_dir():
            logger.error(f"Базова диреторія '{self.repo_path}' не знайдена або не є директорією.")
            return {
                "status": "error",
                "message": f"Базова директорія '{self.repo_path}' не існує або не є директорією.",
            }

        if not diff_content.strip():
            logger.info("Спроба застосувати порожній diff. Змін не буде.")
            return {"status": "success", "message": "Порожній diff, змін не зроблено."}

        if patch_ng is None:
            logger.error("Бібліотека 'patch-ng' не встановлена. Неможливо застосувати diff.")
            return {"status": "error", "message": "Бібліотека 'patch-ng' не встановлена."}

        try:
            patches = patch_ng.fromstring(diff_content)

            if not patches:
                logger.warning("Не знайдено валідних патчів у наданому diff.")
                return {"status": "skipped", "message": "Не знайдено валідних патчів."}

            # strip=1 є типовим для git-стилю diffs (наприклад, 'a/file.py' -> 'file.py').
            success = patches.apply(root=str(base_path), strip=1)

            if success:
                logger.info(f"Diff успішно застосовано до '{base_path}'.")
                return {"status": "success", "message": "Diff успішно застосовано."}
            else:
                logger.error(f"Не вдалося застосувати diff до '{base_path}'. Деякі патчі могли не застосуватися чисто.")
                return {"status": "error", "message": "Не вдалося застосувати diff."}

        except patch_ng.PatchError as e:
            logger.error(f"Помилка парсингу або застосування diff: {e}", exc_info=True)
            return {"status": "error", "message": f"Некоректний diff або помилка застосування патчу: {e}"}
        except OSError as e:
            logger.error(f"Помилка операційної системи під час застосування diff до '{base_path}': {e}", exc_info=True)
            return {"status": "error", "message": f"Помилка файлової системи під час застосування патчу: {e}"}
        except Exception as e:
            logger.critical(f"Неочікувана помилка під час застосування diff: {e}", exc_info=True)
            return {"status": "error", "message": f"Неочікувана помилка: {e}"}
