# print(make_footer(settings, total_runs, successful_runs, equal_stdouts), flush=True)


# def make_footer(settings: Settings, total_runs: int, successful_runs: int,
#                 equal_stdouts: DefaultDict[str, List[int]]) -> str:
#     parts = [OUTPUT_DIVIDER]

#     if settings.show_stats:
#         line = f'{successful_runs}/{total_runs} program{"" if total_runs == 1 else "s"} successfully run'
#         if successful_runs < total_runs:
#             line += f'. {total_runs - successful_runs} failed due to non-zero exit code or timeout.'
#         else:
#             line += '!'
#         parts.append(line)

#     if settings.show_equal:
#         groups = sorted(equal_stdouts.values(), key=len)
#         biggest = len(groups[-1]) if groups else 0
#         line = f'{biggest}/{total_runs} had the exact same stdout'
#         if biggest != total_runs:
#             line += '. Equal runs grouped: ' + ' '.join('[' + ' '.join(map(str, group)) + ']' for group in groups)
#         else:
#             line += '!'
#         parts.append(line)

#     if len(parts) > 1:
#         parts.append(OUTPUT_DIVIDER)

#     return '\n'.join(parts)
