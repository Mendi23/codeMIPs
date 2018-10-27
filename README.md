# codeMIPs

got to [wiki](https://github.com/Mendi23/codeMIPs/wiki)


## Known Issues

### I can't debug the DataQuery.py (DataExtractor)
*Issue:* Even if I have a breakpoint at DataQuery.py
and I saw that the code **should** pass there - the breakpoint doesn't hit.

*Solution:* Pay attention that **the DataExtractor run only once in a lifetime!**
After one run - all the extracted data are getting cached in `Storage_cache`.
Delete the files under `Storage_cache` and all should be solved