FROM docker.io/library/archlinux@sha256:9edcc183d2505745a1da7a18bf12833dde174734610c72a5978031191504af1f

COPY fakeroot.pkg.tar.zst /tmp/fakeroot.pkg.tar.zst
COPY mpdecimal.pkg.tar.zst /tmp/mpdecimal.pkg.tar.zst
COPY python.pkg.tar.zst /tmp/python.pkg.tar.zst

RUN printf '%s  %s\n' \
      f823c52c1450bf59a7fb493564793c61d7827fcba55524b0f5cd8ef41535a823 /tmp/fakeroot.pkg.tar.zst \
      8679f71ed9a982c91883adfaaf0f87a1b74d92d4060283180c4a105a6c7afb19 /tmp/mpdecimal.pkg.tar.zst \
      fda7dc7b67bd316a0e6a18164ffd122599458f4f9736caa0c35a9eb649bade8d /tmp/python.pkg.tar.zst \
    | sha256sum --check --strict \
    && pacman -U --noconfirm \
      /tmp/fakeroot.pkg.tar.zst \
      /tmp/mpdecimal.pkg.tar.zst \
      /tmp/python.pkg.tar.zst \
    && rm /tmp/fakeroot.pkg.tar.zst \
      /tmp/mpdecimal.pkg.tar.zst \
      /tmp/python.pkg.tar.zst

RUN useradd --create-home --uid 1002 builder

USER builder
ENV HOME=/home/builder
ENV SOURCE_DATE_EPOCH=1783975292
WORKDIR /tmp/apx-contracts-reproducible-build

CMD ["makepkg", "--cleanbuild", "--clean", "--force", "--noconfirm"]
