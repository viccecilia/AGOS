(() => {
  const panel = document.getElementById('runtime-collection-compliance-guard');
  if (!panel) throw new Error('Collection Compliance Guard panel missing');
  if (!panel.innerText.includes('write API=false')) throw new Error('write API boundary missing');
  return true;
})();
