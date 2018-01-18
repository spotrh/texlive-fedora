#!/usr/bin/env python3

import argparse
import os
import pickle
import progressbar
import re
import requests
import shutil
import sys
import tarfile
import time
import urllib3
from urllib.parse import urljoin
from urllib.parse import urlparse
from bs4 import BeautifulSoup

found = 0

# Nothing really uses this, we just need to have it.
# TODO: Allow this to be overridden by an argument
tlversion = 20170520
tlrelease = 1
tlepoch = 7

extension = '.tar.xz'

ignore = ['.source.', '.amd64', '.arm', '.i386', '.powerpc', '.sparc', '.win32', '.x86_64' ]
# NOTE
# be careful with these strings, lead them with " and end them with . to eliminate over-aggressive matching
# non-free items
ignore.extend(('"uwmslide.', '"euro-ce.'))
# items packaged separately
# missing dot on asymptote is intentional to get wider match
ignore.extend(('"asymptote', '"biber.', '"latexmk.' '"getafm.', '"psutils.', '"t1utils.', '"texworks.', '"xindy.'))
# items in texlive-base
ignore.extend(('"cyrillic.', '"glyphlist.', '"latex.', '"oberdiek.', '"texlive-en.', '"a2ping.'))
ignore.extend(('"accfonts.', '"adhocfilelist.', '"afm2pl.', '"aleph.', '"amstex.', '"arara.'))
ignore.extend(('"authorindex.', '"autosp.', '"bibexport.', '"bibtex.', '"bibtexu.', '"bibtex8.'))
ignore.extend(('"bundledoc.', '"cachepic.', '"checkcites.', '"checklistings.', '"chktex.'))
ignore.extend(('"cjk-gs-integrate.', '"cjkutils.', '"context.', '"convbkmk.', '"crossrefware.'))
ignore.extend(('"cslatex.', '"csplain.', '"ctanify.', '"ctanupload.', '"ctie.', '"cweb.'))
ignore.extend(('"cyrillic-bin.', '"de-macro.', '"detex.', '"diadia.', '"dosepsbin.', '"dtl.'))
ignore.extend(('"dtxgen.', '"dvi2tty.', '"dviasm.', '"dvicopy.', '"dvidvi.', '"dviljk.'))
ignore.extend(('"dvipdfmx.', '"dvipng.', '"dvipos.', '"dvips.', '"dvisvgm.', '"ebong.'))
ignore.extend(('"eplain.', '"epspdf.', '"epstopdf.', '"exceltex.', '"fig4latex.', '"findhyph.'))
ignore.extend(('"fontinst.', '"fontools.', '"fontware.', '"fragmaster.', '"getmap.', '"glossaries.'))
ignore.extend(('"gregoriotex.', '"gsftopk.', '"installfont.', '"jadetex.', '"kotex-utils.', '"kpathsea.'))
ignore.extend(('"lacheck.', '"latex-git-log.', '"latex-papersize.', '"latex2man.', '"latex2nemeth.', '"latexdiff.'))
ignore.extend(('"latexfileversion.', '"latexindent.', '"latexpand.', '"lcdftypetools.', '"lilyglyphs.', '"listbib.'))
ignore.extend(('"listings-ext.', '"lollipop.', '"ltxfileinfo.', '"ltximg.', '"lua2dox.', '"luaotfload.'))
ignore.extend(('"luatex.', '"lwarp.', '"make4ht.', '"makedtx.', '"makeindex.', '"match_parens.'))
ignore.extend(('"mathspic.', '"metafont.', '"metapost.', '"mex.', '"mflua.', '"mfware.'))
ignore.extend(('"mf2pt1.', '"mkgrkindex.', '"mkjobtexmf.', '"mkpic.', '"mltex.', '"mptopdf.'))
ignore.extend(('"multibibliography.', '"musixtex.', '"musixtnt.', '"m-tx.', '"omegaware.', '"patgen.'))
ignore.extend(('"pax.', '"pdfbook2.', '"pdfcrop.', '"pdfjam.', '"pdflatexpicscale.', '"pdftex.'))
ignore.extend(('"pdftools.', '"pdfxup.', '"pedigree-perl.', '"perltex.', '"petri-nets.', '"pfarrei.'))
ignore.extend(('"pkfix.', '"pkfix-helper.', '"pmx.', '"pmxchords.', '"pstools.', '"pst2pdf.'))
ignore.extend(('"pst-pdf.', '"ps2pk.', '"ptex.', '"ptex-fontmaps.', '"ptex2pdf.', '"purifyeps.'))
ignore.extend(('"pygmentex.', '"pythontex.', '"rubik.', '"seetexk.', '"splitindex.', '"srcredact.'))
ignore.extend(('"sty2dtx.', '"svn-multi.', '"synctex.', '"tetex.', '"tex.', '"tex4ebook.'))
ignore.extend(('"tex4ht.', '"texconfig.', '"texcount.', '"texdef.', '"texdiff.', '"texdirflatten.'))
ignore.extend(('"texdoc.', '"texfot.', '"texlive.infra.', '"texliveonfly.', '"texlive-scripts.', '"texloganalyser.'))
ignore.extend(('"texosquery.', '"texsis.', '"texware.', '"thumbpdf.', '"tie.', '"tpic2pdftex.'))
ignore.extend(('"ttfutils.', '"typeoutfileinfo.', '"ulqda.', '"uptex.', '"urlbst.', '"velthuis.'))
ignore.extend(('"vlna.', '"vpe.', '"web.', '"xdvi.', '"xetex.', '"xmltex.', '"yplan.'))
# Technically, these are not source files in texlive-base
# but that is because they are redundant
ignore.extend(('"latex-bin.', '"cyrillic-bin.'))
blacklist = re.compile('|'.join([re.escape(word) for word in ignore]))

ctanbaseurl = "http://ctan.sharelatex.com/tex-archive/systems/texlive/tlnet/archive/"

ctan_good_items = []

http = urllib3.PoolManager()
site = http.request('GET', ctanbaseurl)
soup = BeautifulSoup(site.data, "lxml")

list_urls = soup.find_all('a')

site.release_conn()

clean_list_urls = [word for word in list_urls if not blacklist.search(str(word))]

def generate_ctan_good_items(ctan_good_items, found):
	print("Generating master list of valid CTAN packages:")
	bar = progressbar.ProgressBar(maxval=len(clean_list_urls)).start()
	for url in clean_list_urls:
		bar.update(found)
		if url['href'].endswith(extension):
			# Check the Content-Length. If it is less than 1024, it is an empty shell.
			true_url = urljoin(ctanbaseurl, url['href'])
			res = requests.head(true_url)
			if int(res.headers['content-length']) > 1024:
				# print url['href']
				# print str(url['href']).replace(extension, '')
				# print str(url['href'])
				# print str(true_url)
				ctan_good_items.append({'name':str(url['href']).replace(extension, ''), 'tarball':str(url['href']), 'ctanurl':str(true_url), 'isdoc':'false', 'justdoc':'false'})
				found += 1
	bar.finish()
	print("Number of valid CTAN packages found:",found)
	# Look for components which are "just doc", components which are not part of a foo & foo.doc pair
	for x in ctan_good_items:
		if '.doc' in x['name']:
			# Hey this is a doc package! Mark it.
			x['isdoc'] = 'true'
			basecomp = re.sub('.doc', '', x['name'])
			if not any(t['name'] == basecomp for t in ctan_good_items):
				print("{} is not part of a component pair, it is just doc".format(x['name']))
				x['justdoc'] = 'true'

def generate_source_list(ctan_good_items, inputargs, specfile):
	if inputargs.verbose:
		print("Writing Source list to spec file.")
	for x in ctan_good_items:
		if 'beebe' in x['name']:
			specfile.write("# Upstream beebe contains non-free files:\n")
			specfile.write("# bibtex/bst/beebe/astron.bst\n")
			specfile.write("# bibtex/bst/beebe/jtb.bst\n")
			specfile.write("# We remove those files from the tarball and make a -clean tarball.\n")
			specfile.write("Source{}: beebe-clean.tar.xz\n".format(ctan_good_items.index(x)))
		else:
			specfile.write("Source{}: {}\n".format(ctan_good_items.index(x), x['ctanurl']))

def generate_preamble(inputargs, specfile):
	if inputargs.verbose:
		print("Writing preamble section to spec file.")
	specfile.write("Name: texlive\n")
	specfile.write("Version: {}\n".format(tlversion))
	specfile.write("Release: {}\n".format(tlrelease))
	specfile.write("Epoch: {}\n".format(tlepoch))
	specfile.write("Summary: TeX formatting system\n")
	# TODO: Autogenerate this from what we find in the subpackages?
	# LOW PRIORITY: We do not care about the validity of this string so much, there is no "texlive" binary package
	specfile.write("License: Artistic 2.0 and GPLv2 and GPLv2+ and LGPLv2+ and LPPL and MIT and Public Domain and UCD and Utopia\n")
	specfile.write("URL: http://tug.org/texlive/\n")
	# We should not have any BuildRequires here.
	specfile.write("BuildArch: noarch\n")

def generate_prep_section(inputargs, specfile):
	if inputargs.verbose:
		print("Writing %prep section to spec file.")
	specfile.write("\n")
	specfile.write("%prep\n")
	specfile.write("%setup -q -c -T\n\n")
	specfile.write("#this macro has to be here, not at the top, or it will not evaluate properly. :P\n")
	specfile.write('%global mysources %{lua: for index,value in ipairs(sources) do if index >= 1 then print(value.." ") end end}\n')
	specfile.write("\n")

def generate_build_section(inputargs, specfile):
	if inputargs.verbose:
		print("Writing %build section to spec file.")
	specfile.write("%build\n")
	specfile.write("\n")

def generate_install_section(inputargs, specfile):
	if inputargs.verbose:
		print("Writing %install section to spec file.")
	specfile.write("%install\n")
	specfile.write("pushd %{buildroot}%{_texdir}\n")
	specfile.write("for noarchsrc in %{mysources}; do\n")
	specfile.write("  xz -dc $noarchsrc | tar x\n")
	specfile.write("done\n")
	specfile.write("popd\n")
	specfile.write("\n")

def download_and_unpack(ctan_good_items, inputargs, specfile):
	print("Downloading and unpacking valid CTAN packages into components/:")
	bar = progressbar.ProgressBar(maxval=len(ctan_good_items)).start()
	for x in ctan_good_items:
		bar.update(ctan_good_items.index(x))
		my_tarball_path = os.path.join('components', str(x['tarball']))
		# print(my_tarball_path)
		try:
			my_http = urllib3.PoolManager()
			with my_http.request('GET', x['ctanurl'], preload_content=False) as r, open(my_tarball_path, 'wb') as local_file:
				shutil.copyfileobj(r, local_file)
		except HTTPError as e:
			print("HTTP Error: {} {}".format(e.code, x['ctanurl']))
			alldone(specfile)
		except URLError as e:
			print("URL Error: {} {}".format(e.reason, x['ctanurl']))
			alldone(specfile)

		tar = tarfile.open(my_tarball_path, "r:xz")
		os.makedirs(os.path.join('components', str(x['name'])))
		tar.extractall(path=os.path.join('components', str(x['name'])))
		tar.close()

		# need to repack beebe into clean version
		if 'beebe' in x['name']:
			os.remove(os.path.join('components', str(x['name']), 'bibtex/bst/beebe/astron.bst'))
			os.remove(os.path.join('components', str(x['name']), 'bibtex/bst/beebe/jtb.bst'))
			beebe_clean_tar = tarfile.open(os.path.join('components', 'beebe-clean.tar.xz'), "w:xz")
			beebe_clean_tar.add(os.path.join('components', str(x['name'])), arcname='.')
			beebe_clean_tar.close()
			# Remove unclean tar
			os.remove(os.path.join('components', str(x['tarball'])))
	bar.finish()

def generate_file_lists(ctan_good_items, inputargs, specfile):
	# TODO: WHAT IS GOING WRONG WITH amsmath?
	# TODO: Drop newline after %files if component has a doc pair.
	print("Generating file lists for valid CTAN packages:")
	# TODO: print %license 
	# TODO: hardcode checks for corner cases which are not just dirs
	for x in ctan_good_items:
		if x['isdoc'] == 'true':
			if x['justdoc'] == 'true':
				specfile.write("%files {}\n".format(str(x['name'])))
		else:
			specfile.write("%files {}\n".format(str(x['name'])))
		lowest_dirs = list()
		base_path = os.path.join('components', str(x['name']))
		for root,dirs,files in os.walk(base_path):
			if not dirs and 'tlpkg' not in root:
				lowest_dirs.append(os.path.relpath(root, base_path))

		# Explicitly adding this helps.
		if x['isdoc'] == 'true':
			basecomp = re.sub('.doc', '', x['name'])
			latexdocexplicit = os.path.join('doc/latex', basecomp)
			# print("checking for {}".format(latexdocexplicit))
			for i in lowest_dirs:
				if latexdocexplicit in i:
					print("adding {}".format(latexdocexplicit))
					lowest_dirs.append(latexdocexplicit)
					break
			fontsdocexplicit = os.path.join('doc/fonts', basecomp)
			for i in lowest_dirs:
				if fontsdocexplicit in i:
					lowest_dirs.append(fontsdocexplicit)
					break
		# TODO: Non font cases.

		lowest_dirs.sort()
		while lowest_dirs:
			common_among_all = os.path.commonprefix(lowest_dirs)
			if common_among_all and common_among_all != "tex/" and common_among_all != "fonts/" and "bibtex" not in common_among_all:
				if x['isdoc'] == 'true':
					specfile.write("%doc %{{_texdir}}/texmf-dist/{}\n".format(common_among_all))
				else:
					specfile.write("%{{_texdir}}/texmf-dist/{}\n".format(common_among_all))
				break
			else:
				bottom_dir = lowest_dirs.pop()
				if x['isdoc'] == 'true':
					specfile.write("%doc %{{_texdir}}/texmf-dist/{}\n".format(bottom_dir))
				else:
					specfile.write("%{{_texdir}}/texmf-dist/{}\n".format(bottom_dir))

		# common_among_all = os.path.commonprefix(lowest_dirs)
		# if common_among_all and common_among_all != "tex/" and common_among_all != "fonts/" :
			# print("for component {}, common dir {} found".format(str(x['name']), common_among_all))
		#	specfile.write("%{{_texdir}}/texmf-dist/{}\n".format(common_among_all))
		# else:
		# 	for dir in lowest_dirs:
		#		specfile.write("%{{_texdir}}/texmf-dist/{}\n".format(dir))
		specfile.write("\n")


def alldone(specfile):
	specfile.close()
	sys.exit(0)

# Time to make a new texlive.spec
if os.path.isfile("texlive.spec"):
	print("texlive.spec is already here, move it first please")
	sys.exit(0)
else:
	specfile = open("texlive.spec", "w+")

parser = argparse.ArgumentParser(description='Do the magic to make the Fedora texlive.spec file.')
parser.add_argument("--readdict", help="Read valid CTAN dictionary from a file", action="store", dest="read_dict_file_location")
parser.add_argument("--savedict", help="Save valid CTAN dictionary to a file", action="store", dest="dict_file_location")
parser.add_argument("--usecache", help="Use cache for unpacked components", action='store_true')
parser.add_argument("--verbose", help="Be verbose about what is happening", action='store_true')
inputargs = parser.parse_args()

if inputargs.dict_file_location:
	if inputargs.read_dict_file_location:
		print("Can not use --readdict with --savedict. Exiting.")
		alldone(specfile)
	if inputargs.verbose:
		print("Generating valid CTAN dictionary from upstream sources.")
	generate_ctan_good_items(ctan_good_items, found)
	if inputargs.verbose:
		print("Saving valid CTAN dictionary to {}".format(inputargs.dict_file_location))
	with open(inputargs.dict_file_location, 'wb') as f:
		pickle.dump(ctan_good_items, f)
else:
	if inputargs.read_dict_file_location:
		if inputargs.verbose:
			print("Reading CTAN dictionary from {}".format(inputargs.read_dict_file_location))
			print("File last modified on {}".format(time.ctime(os.path.getmtime(inputargs.read_dict_file_location))))
		with open(inputargs.read_dict_file_location, 'rb') as f:
			ctan_good_items = pickle.load(f)
	else:
		generate_ctan_good_items(ctan_good_items, found)

# force sort
ctan_good_items = sorted(ctan_good_items, key=lambda k: k['name'])

if os.path.exists("components"):
	if not inputargs.usecache:
		print("Components directory exists! Please remove and restart, or pass --usecache.")
		alldone(specfile)
else:
	os.makedirs("components")

if inputargs.usecache:
	print("Using cache, skipping download and unpacking loop")
else:
	download_and_unpack(ctan_good_items, inputargs, specfile)
generate_preamble(inputargs, specfile)
generate_source_list(ctan_good_items, inputargs, specfile)
# TODO SUBPACKAGES (to be fair, that's 99% of this spec file)
# need to make a working dir to unpack things into
generate_prep_section(inputargs, specfile)
generate_build_section(inputargs, specfile)
generate_install_section(inputargs, specfile)
# TODO: FILES SECTIONS
generate_file_lists(ctan_good_items, inputargs, specfile)

# Spec file done!
alldone(specfile)

# TODO
# generate subpackage list
# - some packages are doc only
# - some packages have both (and if so, we want to combine them)
# Generate subpackage entry
#  - svn ver
#  - license
#  - deps 
# Generate files entry
#  - can we make it simple or does it need to be file by file?
