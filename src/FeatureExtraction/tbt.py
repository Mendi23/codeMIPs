import sys



from utils.file_paths import EXAMPLE_PATH

sys.argv = [__file__, '-i', EXAMPLE_PATH]
import pycflow2dot as cg
cg.main()
