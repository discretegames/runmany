print(make_footer(settings, total_runs, successful_runs, equal_stdouts), flush=True)


OUTPUT_FILL_CHAR, OUTPUT_FILL_WIDTH = '-', 60
OUTPUT_DIVIDER = OUTPUT_FILL_WIDTH * '*'

  @staticmethod
   def make_output_part(title: str, section: Section, content: Optional[str] = None) -> str:
        if content is None:
            content = section.content.strip('\r\n')
        return f'{f" {title} line {section.line_number} ":{OUTPUT_FILL_CHAR}^{OUTPUT_FILL_WIDTH}}\n{content}'

    def make_output(self, run_number: int, time_taken: float,  # pylint: disable=too-many-arguments
                    exit_code: Union[int, str], command: str, stdout: str) -> str:
        parts = [OUTPUT_DIVIDER]

        headline = f'{run_number}. {self.language_data.name}'
        if self.language_data.show_time:
            headline += f' ({time_taken:.2f}s)'
        if exit_code != 0:
            headline += f' [exit code {exit_code}]'
        if self.language_data.show_command:
            headline += f' > {command}'
        parts.append(headline)

        if self.language_data.show_code:
            parts.append(self.make_output_part('code at', self.code_section))
        if self.argv_section and self.argv_section.content and self.language_data.show_argv:
            parts.append(self.make_output_part('argv at', self.argv_section))
        if self.stdin_section and self.stdin_section.content and self.language_data.show_stdin:
            parts.append(self.make_output_part('stdin at', self.stdin_section))
        if self.language_data.show_output:
            parts.append(self.make_output_part('output from', self.code_section, stdout))

        return '\n'.join(parts) + '\n' * cast(int, self.language_data.spacing)


def make_footer(settings: Settings, total_runs: int, successful_runs: int,
                equal_stdouts: DefaultDict[str, List[int]]) -> str:
    parts = [OUTPUT_DIVIDER]

    if settings.show_stats:
        line = f'{successful_runs}/{total_runs} program{"" if total_runs == 1 else "s"} successfully run'
        if successful_runs < total_runs:
            line += f'. {total_runs - successful_runs} failed due to non-zero exit code or timeout.'
        else:
            line += '!'
        parts.append(line)

    if settings.show_equal:
        groups = sorted(equal_stdouts.values(), key=len)
        biggest = len(groups[-1]) if groups else 0
        line = f'{biggest}/{total_runs} had the exact same stdout'
        if biggest != total_runs:
            line += '. Equal runs grouped: ' + ' '.join('[' + ' '.join(map(str, group)) + ']' for group in groups)
        else:
            line += '!'
        parts.append(line)

    if len(parts) > 1:
        parts.append(OUTPUT_DIVIDER)

    return '\n'.join(parts)
