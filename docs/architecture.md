# Расширенная архитектура CLI интерпретатора

```mermaid
classDiagram
    class Command {
        <<interface>>
        +execute(args: list[str], stdin: Optional[IO]) tuple[int, Optional[str]]
    }
    
    class CatCommand {
        +execute(args, stdin)
    }
    
    class EchoCommand {
        +execute(args, stdin)
    }
    
    class WcCommand {
        +execute(args, stdin)
    }
    
    class PwdCommand {
        +execute(args, stdin)
    }
    
    class ExitCommand {
        +execute(args, stdin)
    }
    
    class DefaultCommand {
        +execute(args, stdin)
    }
    
    class CLIManager {
        -executor: Executor
        -parser: Parser
        +start()
        -process_input(input: str) int
    }
    
    class Parser {
        -substitution_handler: SubstitutionHandler
        +parse(line: str) ParsedInput
        -parse_command(cmd_str: str) ParsedCommand
    }
    
    class Executor {
        -registry: CommandRegistry
        -pipeline: PipelineEngine
        +execute(commands: ParsedInput) int
    }
    
    class CommandRegistry {
        -commands: Dict[str, Type[Command]]
        +get_command(name: str) Command
    }
    
    class PipelineEngine {
        +run_pipeline(commands: list[ParsedCommand]) int
        -create_pipes()
        -redirect_streams()
    }
    
    class SubstitutionHandler {
        +process(input: str) str
        -resolve_var(name: str) str
        -resolve_cmd(cmd: str) str
    }
    
    Command <|-- CatCommand
    Command <|-- EchoCommand
    Command <|-- WcCommand
    Command <|-- PwdCommand
    Command <|-- ExitCommand
    Command <|-- DefaultCommand
    
    CLIManager --> Parser
    CLIManager --> Executor
    Executor --> CommandRegistry
    Executor --> PipelineEngine
    Parser --> SubstitutionHandler

1. Пользовательский ввод → CLIManager
2. CLIManager → Parser (разбор команды)
3. Parser → Executor (передача ParsedInput) 
4. Executor ↔ CommandRegistry (получение обработчиков)
5. Executor → PipelineEngine (управление пайпами)
6. PipelineEngine ↔ Команды (исполнение в процессах)
7. Результат → CLIManager → Пользователю


## Описание

* `CLIManager`
  * Управляет интерпретатором, запускает парсинг и исполнение команд
* `Parser`
  * Парсит входную строку на токены, учитывая заданные требования
  * Результат функции `parse` - список списков. Каждый из списков - команда, разделенная на токены, команды разделены пайплайном. Например:
    * `parse("echo 123") -> [["echo", "123"]]`
    * `parse("echo 123 | wc") -> [["echo", "123"], ["wc"]]`
* `Executor`
  * Получает команды из `Parser` и выполняет их
  * Для этого используются:
    * `Command`
      * Интерфейс для известных команд
      * `execute(args: list[str])` - функция для исполнения команды, разбитой на токены
    * Для известных команд (`cat, echo, wc, pwd, exit`) есть соответствующие классы, реализующие интерфейс `Command` (например, `CatCommand`)
    * Для неизвестных команд класс `DefaultCommand`, который исполняет эту команду как внешнюю программу
  * Для осуществления работы с пайплайнами используются `fork()` и `pipe`

* `Pipes`
  * Технологии:

    * os.fork() - создание процессов

    * os.pipe() - межпроцессное взаимодействие

    * os.dup2() - перенаправление потоков

* Схема выполнения:

  ![Схема выполнения](./images/pipes.png)

* `Substitunions`
* Поддерживаемые форматы:
  * 1. Простые: $HOME
 
  * 2. Фигурные скобки: ${PATH}

  * 3. Командная подстановка: `date`

* Алгоритм обработки
  * 1. Сканирование строки на шаблоны

  * 2. Поиск значений в:

    * 1. Окружении (os.environ)

    * 2. Кэше интерпретатора

    * 3. Результатах выполнения команд

  * 3. Замена с учетом экранирования (\$)  
