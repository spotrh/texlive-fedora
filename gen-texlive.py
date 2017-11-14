#!/usr/bin/env python

import argparse
import os
import pickle
import progressbar
import re
import requests
import sys
import time
import urllib2
import urlparse
from bs4 import BeautifulSoup

found = 0

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

site = urllib2.urlopen(ctanbaseurl)
html = site.read()
soup = BeautifulSoup(html, "lxml")

list_urls = soup.find_all('a')

clean_list_urls = [word for word in list_urls if not blacklist.search(str(word))]

def generate_ctan_good_items(ctan_good_items, found):
	print("Generating master list of valid CTAN packages:")
	bar = progressbar.ProgressBar(maxval=len(clean_list_urls)).start()
	for url in clean_list_urls:
		bar.update(found)
		if url['href'].endswith(extension):
			# Check the Content-Length. If it is less than 1024, it is an empty shell.
			true_url = urlparse.urljoin(ctanbaseurl, url['href'])
			res = requests.head(true_url)
			if int(res.headers['content-length']) > 1024:
				# print url['href']
				# print str(url['href']).replace(extension, '')
				# print str(url['href'])
				# print str(true_url)
				ctan_good_items.append({'name':str(url['href']).replace(extension, ''), 'tarball':str(url['href']), 'ctanurl':str(true_url), 'sourcenum':found+1})
				found += 1
	bar.finish()
	print("Number of valid CTAN packages found:",found)

def generate_source_list(ctan_good_items, inputargs, specfile):
	if inputargs.verbose:
		print("Writing Source list to spec file.")
	for x in ctan_good_items:
		if 'beebe' in x['name']:
			specfile.write("# Upstream beebe contains non-free files:\n")
			specfile.write("# bibtex/bst/beebe/astron.bst\n")
			specfile.write("# bibtex/bst/beebe/jtb.bst\n")
			specfile.write("# We remove those files from the tarball and make a -clean tarball.\n")
			specfile.write("Source{}: beebe-clean.tar.xz\n".format(x['sourcenum']))
		else:
			specfile.write("Source{}: {}\n".format(x['sourcenum'], x['ctanurl']))

# Time to make a new texlive.spec
if os.path.isfile("texlive.spec"):
	print("texlive.spec is already here, move it first please")
	sys.exit(0)
else:
	specfile = open("texlive.spec", "w+")

parser = argparse.ArgumentParser(description='Do the magic to make the Fedora texlive.spec file.')
parser.add_argument("--readdict", help="Read valid CTAN dictionary from a file", action="store", dest="read_dict_file_location")
parser.add_argument("--savedict", help="Save valid CTAN dictionary to a file", action="store", dest="dict_file_location")
parser.add_argument("--verbose", help="Be verbose about what is happening", action='store_true')
inputargs = parser.parse_args()
print inputargs

if inputargs.dict_file_location:
	if inputargs.read_dict_file_location:
		print("Can not use --readdict with --savedict. Exiting.")
		sys.exit(0)
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

generate_source_list(ctan_good_items, inputargs, specfile)

# Spec file done!

specfile.close()

# TODO
# generate subpackage list
# - some packages are doc only
# - some packages have both (and if so, we want to combine them)
# Download files
# Unpack files
# Generate subpackage entry
#  - svn ver
#  - license
#  - deps 
# Generate files entry
#  - can we make it simple or does it need to be file by file?


# TODO
# clean non-free files from beebe.tar.xz
# bibtex/bst/beebe/astron.bst
# bibtex/bst/beebe/jtb.bst
# We must remove those files from the tarball and make a "-clean" tarball.

