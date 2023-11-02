# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2021 Neongecko.com Inc.
# BSD-3
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

charts_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/../helm-charts"
cd "$(dirname "${charts_dir}" )" || exit 0

helm repo add diana https://neongeckocom.github.io/neon-diana-utils
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add jetstack https://charts.jetstack.io
helm repo add bitnami https://charts.bitnami.com/bitnami

git clone https://github.com/NeonGeckoCom/neon-diana-utils -b helm-charts helm-charts > /dev/null
cd "${charts_dir}" || exit 10

# Remove all lock files
rm ../neon_diana_utils/helm_charts/*/*/Chart.lock

# Package Base libraries
for d in ../neon_diana_utils/helm_charts/base/*; do
  helm dependency update "${d}" > /dev/null
done
helm package ../neon_diana_utils/helm_charts/base/*

# Package HTTP Services
for d in ../neon_diana_utils/helm_charts/http/*; do
  helm dependency update "${d}" > /dev/null
done
helm package ../neon_diana_utils/helm_charts/http/*

# Package MQ Services
for d in ../neon_diana_utils/helm_charts/mq/*; do
  helm dependency update "${d}"
done
helm package ../neon_diana_utils/helm_charts/mq/*

# Package Backend
for d in ../neon_diana_utils/helm_charts/backend/*-services; do
  helm dependency update "${d}" > /dev/null
done
helm package ../neon_diana_utils/helm_charts/backend/*-services
helm dependency update ../neon_diana_utils/helm_charts/backend/diana-backend > /dev/null
helm package ../neon_diana_utils/helm_charts/backend/*

# Package Neon
for d in ../neon_diana_utils/helm_charts/neon/neon-*; do
  helm dependency update "${d}" > /dev/null
done
helm package ../neon_diana_utils/helm_charts/neon/neon-*
helm dependency update ../neon_diana_utils/helm_charts/neon/core > /dev/null
helm package ../neon_diana_utils/helm_charts/neon/*

# Package Klat
for d in ../neon_diana_utils/helm_charts/klat/*; do
  helm dependency update "${d}" > /dev/null
done
helm package ../neon_diana_utils/helm_charts/klat/*

# Make sure existing charts aren't touched (new charts get new versions)
git reset --hard HEAD

# Update index.yaml and push changes
helm repo index --url https://neongeckocom.github.io/neon-diana-utils .
git add .
git commit -m "Update Helm Charts"
git push
cd .. && rm -rf helm-charts
