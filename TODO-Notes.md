# Moving VNFD & NSD descriptors to SOL0006 compatibility.

 (Berlin, 2021-07-06)

## Background

Seems, the 5Genesis VNFD & NSD descriptor files, as provided in "robottest",
are only supported by pre-version-9 OSM.  At least in version 9 OSM, VNFD
descriptors need to be SOL0006 compatible.

It is possible to translate the test files, as provided in "robottest", to the
newer "format" but, now, also the code base of MANO Wrapper needs to be
adjusted -- bummer!

## How to translate the files

 (Note: Using `tar` directly, is just my approach in getting it to work.
  Maybe, a more "proper" (TM) way of doing this exist, I wouldn't know.)

```
tar xf <vnfd_package|/nsd_package>.tar.gz
# Result: vnfd_package/ and nsd_package/ dirs are created

osm package-translate vnfd_package/
osm package-translate nsd_package/

# Repackage using tar
tar czf <vnfd_package|nsd_package>.tar.gz <vnfd_package/|/nsd_package/>
```

## Notes about the current commits and approach

Of the SOL0006-compatible descriptor files only NSDs can be successfully
"indexed" (uploaded to the MANO wrapper), **for now**.  You can still index the
old VNFD files.  Since the NSDs refer to existing VNFDs, this will be needed to
get this working correctly.

NOTE: To be able to also successfully onboard an NSD (via Swagger API)
following work around (for now) can be used:

  1. Make sure the NSD and its depended VNFDs are indexed properly (within the
     MANO Wrapper)
  2. Use the SOL0006-compatible (translated) VNFD descriptor files to upload
     these to the OSM, by using the `osm` binary (on your host where the OSM is
     running)
     - e.g. `osm vnfd-create hackfest_1_nsd_sol006.tar.gz`
     - check using `osm vnfd-list`
     - check details using `osm vnfd-show hackfest1_nsd`
  3. Use the Swagger API of Dispatcher to onboard the NSD.
  4. Result:
     - Returns a 201 code in Dispatcher Swagger API 
     - At OSM host, the onboarded NSD can be observed by using `osm nsd-list`

## Additional notes

Within current version, the VNFD and NSD descriptor are *not* validated during
indexing (code is defunct for now), simply due to the fact that the current
JSON schema doesn't fit the SOL0006 descriptors.

Only the "hackfest1" examples were tested, and hacked into the code.
Most probably, more generic/complex VNFDs and NSDs won't work with the
current code adjustements.

