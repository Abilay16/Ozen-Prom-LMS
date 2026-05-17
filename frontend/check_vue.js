const { parse, compileScript, compileTemplate } = require('@vue/compiler-sfc')
const fs = require('fs')
const src = fs.readFileSync('/app/src/pages/admin/ProtocolDetailPage.vue', 'utf8')
const { descriptor, errors } = parse(src)
if (errors.length) {
  console.log('PARSE ERRORS:')
  errors.forEach(e => console.log(e.message, 'at', e.loc))
} else {
  console.log('Parse OK, template starts at line:', descriptor.template?.loc?.start?.line)
  // Try compiling the template
  try {
    const t = compileTemplate({ source: descriptor.template.content, id: 'test', filename: 'test.vue' })
    if (t.errors.length) {
      console.log('TEMPLATE ERRORS:')
      t.errors.forEach(e => console.log(e.message, e.loc))
    } else {
      console.log('Template OK')
    }
  } catch(e2) {
    console.log('Template compile error:', e2.message)
  }
  // Try compiling the script
  try {
    const s = compileScript(descriptor, { id: 'test' })
    console.log('Script OK')
  } catch(e3) {
    console.log('Script compile error:', e3.message)
  }
}
