from setuptools import setup, find_packages

setup(
    name='django-foundation',
    version='0.1',
    description='The Zurb Foundation responsive framework, along with templates and useful tags.',
    long_description=open('README.md').read(),
    author='Silvio J. Gutierrez',
    author_email='silviogutierrez@gmail.com',
    url='https://github.com/silviogutierrez/django-foundation-scss',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
