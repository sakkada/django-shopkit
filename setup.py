#! /usr/bin/env python
from setuptools import setup, find_packages

# dynamic retrive version number from stachless.VERSION
version = __import__('shopkit').__version__

CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.5',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Topic :: Internet :: WWW/HTTP',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

REQUIREMENTS = [
    'Django >= 1.8.0',
    # 'django-mptt >= 0.4.2',
    'prices >= 0.5,<0.6a0',
    'django-prices >=0.4.0,<0.5a0'
]

EXTRAS = {
#     'authorize.net payment provider': [
#         'django-authorizenet >= 1.0',
#         'unidecode'
#     ],
#     'django-payments payment provider': [
#         'django-payments'
#     ],
#     'mamona payment provider': [
#         'mamona',
#     ],
#     'stripe payment provider': [
#         'stripe',
#     ],
}

setup(name='shopkit',
      author='Guchetl Murat',
      author_email='gmurka@gmail.com',
      description=('An e-commerence framework for Django,'
                   ' based on old-style satchless framework'),
      license='BSD',
      version=version,
      url='http://satchless.com/',
      packages=find_packages(exclude=['docs*', 'demo*',]),
      include_package_data=True,
      classifiers=CLASSIFIERS,
      install_requires=REQUIREMENTS,
      extras_require=EXTRAS,
      platforms=['any'],
      zip_safe=False)
