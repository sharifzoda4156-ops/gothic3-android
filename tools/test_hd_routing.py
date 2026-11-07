"""Exercise the patched game JAR on a JVM with a desktop PNG decoder.

Requires a JDK, or --ecj /path/to/ecj.jar and a Java runtime.
"""
import argparse
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ecj', type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory)
        jar = ROOT / 'app/libs/gothic3-classes.jar'
        sources = [ROOT / ('app/src/main/java/' + n + '.java') for n in ('GothicAssets', 'GothicResolution', 'GothicCharacters', 'GothicAnimation')]
        sources += sorted((ROOT / 'tests/hd_runtime').rglob('*.java'))
        compiler = ['java', '-jar', str(args.ecj), '-17'] if args.ecj else ['javac', '--release', '17']
        subprocess.run(compiler + ['-classpath', str(jar), '-d', str(output)]
                       + list(map(str, sources)), check=True)
        resources = ROOT / 'app/src/midlet/resources'
        classpath = os.pathsep.join(map(str, (output, jar, resources)))
        subprocess.run(['java', '-Xverify:all', '-Djava.awt.headless=true', '-classpath', classpath,
                        'HdRoutingTest', str(resources)], check=True)
        for test in ('WholeHeroTest', 'AnimationPackTest'):
            subprocess.run(['java', '-Xverify:all', '-Djava.awt.headless=true', '-classpath', classpath, test], check=True)


if __name__ == '__main__':
    main()
